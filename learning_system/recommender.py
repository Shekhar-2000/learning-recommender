# learning_system/recommender.py
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from collections import defaultdict
import networkx as nx
from django.db.models import Q, Avg, Count
from .models import Course, QuizPerformance, StudentProfile, Engagement, AssessmentResult

class AdvancedRecommender:
    def __init__(self):
        self.course_similarity_matrix = None
        self.user_similarity_matrix = None
        self.knowledge_graph = None
        self._build_knowledge_graph()
    
    def _build_knowledge_graph(self):
        """Build a knowledge graph of skills and course relationships"""
        self.knowledge_graph = nx.DiGraph()
        
        # Add courses as nodes
        courses = Course.objects.all()
        for course in courses:
            self.knowledge_graph.add_node(course.id, 
                                        type='course', 
                                        title=course.title,
                                        tags=course.tags.split(',') if course.tags else [])
        
        # Add skill relationships based on course tags
        for course in courses:
            if course.tags:
                tags = [tag.strip().lower() for tag in course.tags.split(',')]
                for tag in tags:
                    if tag not in self.knowledge_graph:
                        self.knowledge_graph.add_node(tag, type='skill')
                    self.knowledge_graph.add_edge(course.id, tag, weight=1.0)
    
    def get_collaborative_recommendations(self, student, n_recommendations=5):
        """Collaborative filtering based on similar students"""
        try:
            # Get all student performance data
            performances = QuizPerformance.objects.select_related('student', 'quiz__lesson__course').all()
            
            if not performances.exists():
                return self._get_fallback_recommendations()
            
            # Create user-item matrix
            data = []
            for perf in performances:
                data.append({
                    'student_id': perf.student.id,
                    'course_id': perf.quiz.lesson.course.id,
                    'score': perf.score,
                    'engagement': self._calculate_engagement_score(perf.student, perf.quiz.lesson.course)
                })
            
            df = pd.DataFrame(data)
            
            # Create user-item matrix
            user_item_matrix = df.pivot_table(
                index='student_id', 
                columns='course_id', 
                values='score', 
                fill_value=0
            )
            
            # Calculate user similarity
            user_similarity = cosine_similarity(user_item_matrix)
            user_similarity_df = pd.DataFrame(
                user_similarity, 
                index=user_item_matrix.index, 
                columns=user_item_matrix.index
            )
            
            # Get similar students
            student_id = student.id
            if student_id not in user_similarity_df.index:
                return self._get_fallback_recommendations()
            
            similar_students = user_similarity_df[student_id].sort_values(ascending=False)[1:6]
            
            # Get courses liked by similar students
            recommended_courses = set()
            for similar_student_id, similarity in similar_students.items():
                if similarity > 0.1:  # Minimum similarity threshold
                    student_courses = user_item_matrix.loc[similar_student_id]
                    top_courses = student_courses[student_courses > 70].index.tolist()
                    recommended_courses.update(top_courses)
            
            # Remove courses already taken by the student
            student_courses = QuizPerformance.objects.filter(student=student).values_list('quiz__lesson__course_id', flat=True)
            recommended_courses = [c for c in recommended_courses if c not in student_courses]
            
            return Course.objects.filter(id__in=list(recommended_courses)[:n_recommendations])
            
        except Exception as e:
            print(f"Error in collaborative filtering: {e}")
            return self._get_fallback_recommendations()
    
    def get_content_based_recommendations(self, student, n_recommendations=5):
        """Content-based filtering using course features"""
        try:
            # Get student's performance history
            student_performances = QuizPerformance.objects.filter(student=student)
            
            if not student_performances.exists():
                return self._get_fallback_recommendations()
            
            # Analyze student preferences
            student_preferences = self._analyze_student_preferences(student)
            
            # Get all courses
            all_courses = Course.objects.all()
            
            # Calculate similarity scores
            course_scores = []
            for course in all_courses:
                score = self._calculate_content_similarity(course, student_preferences)
                course_scores.append((course, score))
            
            # Sort by score and return top recommendations
            course_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Filter out already taken courses
            taken_courses = set(student_performances.values_list('quiz__lesson__course_id', flat=True))
            recommendations = [course for course, score in course_scores 
                            if course.id not in taken_courses and score > 0][:n_recommendations]
            
            return recommendations
            
        except Exception as e:
            print(f"Error in content-based filtering: {e}")
            return self._get_fallback_recommendations()
    
    def get_hybrid_recommendations(self, student, n_recommendations=5):
        """Combine collaborative and content-based filtering"""
        try:
            # Get recommendations from both methods
            collab_recs = self.get_collaborative_recommendations(student, n_recommendations)
            content_recs = self.get_content_based_recommendations(student, n_recommendations)
            
            # Combine and rank recommendations
            all_recs = list(collab_recs) + list(content_recs)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_recs = []
            for rec in all_recs:
                if rec.id not in seen:
                    seen.add(rec.id)
                    unique_recs.append(rec)
            
            return unique_recs[:n_recommendations]
            
        except Exception as e:
            print(f"Error in hybrid recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def get_knowledge_graph_recommendations(self, student, n_recommendations=5):
        """Use knowledge graph to find related skills and courses"""
        try:
            # Get student's skill profile from assessment
            assessment_result = AssessmentResult.objects.filter(student=student).first()
            if not assessment_result:
                return self._get_fallback_recommendations()
            
            # Get student's strong skills
            strong_skills = [skill for skill, score in assessment_result.skill_scores.items() if score > 60]
            
            if not strong_skills:
                return self._get_fallback_recommendations()
            
            # Find related skills in knowledge graph
            related_skills = set()
            for skill in strong_skills:
                if skill in self.knowledge_graph:
                    # Find skills connected to this skill
                    neighbors = list(self.knowledge_graph.neighbors(skill))
                    related_skills.update(neighbors)
            
            # Find courses related to these skills
            recommended_courses = set()
            for skill in related_skills:
                if skill in self.knowledge_graph:
                    # Find courses connected to this skill
                    course_neighbors = [node for node in self.knowledge_graph.neighbors(skill) 
                                      if self.knowledge_graph.nodes[node].get('type') == 'course']
                    recommended_courses.update(course_neighbors)
            
            # Filter out already taken courses
            taken_courses = QuizPerformance.objects.filter(student=student).values_list('quiz__lesson__course_id', flat=True)
            recommended_courses = [c for c in recommended_courses if c not in taken_courses]
            
            return Course.objects.filter(id__in=list(recommended_courses)[:n_recommendations])
            
        except Exception as e:
            print(f"Error in knowledge graph recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def _analyze_student_preferences(self, student):
        """Analyze student's learning preferences and patterns"""
        preferences = {
            'preferred_tags': defaultdict(int),
            'difficulty_preference': 'beginner',
            'learning_style': 'visual'
        }
        
        # Analyze from quiz performances
        performances = QuizPerformance.objects.filter(student=student).select_related('quiz__lesson__course')
        
        for perf in performances:
            course = perf.quiz.lesson.course
            if course.tags:
                tags = [tag.strip().lower() for tag in course.tags.split(',')]
                for tag in tags:
                    preferences['preferred_tags'][tag] += perf.score / 100.0
        
        # Get difficulty preference from assessment
        assessment_result = AssessmentResult.objects.filter(student=student).first()
        if assessment_result:
            preferences['difficulty_preference'] = assessment_result.learning_level
        
        return preferences
    
    def _calculate_content_similarity(self, course, student_preferences):
        """Calculate similarity between course and student preferences"""
        score = 0.0
        
        if course.tags:
            course_tags = [tag.strip().lower() for tag in course.tags.split(',')]
            
            # Tag-based similarity
            for tag in course_tags:
                if tag in student_preferences['preferred_tags']:
                    score += student_preferences['preferred_tags'][tag]
        
        return score
    
    def _calculate_engagement_score(self, student, course):
        """Calculate engagement score for a student-course pair"""
        try:
            engagements = Engagement.objects.filter(student=student, lesson__course=course)
            if not engagements.exists():
                return 0.0
            
            total_time = sum(eng.time_spent_seconds for eng in engagements)
            completion_rate = sum(1 for eng in engagements if eng.completion_status == 'completed') / len(engagements)
            
            return (total_time / 3600.0) * completion_rate  # Hours * completion rate
            
        except:
            return 0.0
    
    def _get_fallback_recommendations(self):
        """Fallback recommendations when other methods fail"""
        return Course.objects.all()[:5]

# Legacy function for backward compatibility
def get_recommendations(student):
    """Legacy function - now uses advanced recommender"""
    recommender = AdvancedRecommender()
    return recommender.get_hybrid_recommendations(student)