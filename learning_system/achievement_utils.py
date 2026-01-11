"""
Utility functions for awarding achievements automatically.
"""
from .models import (
    StudentProfile, QuizPerformance, CourseCompletion, 
    Achievement, StudentAchievement, Notification, Course, Lesson
)
from django.db.models import Count, Avg, Sum
import uuid

def check_and_award_achievements(student_profile):
    """
    Check if student qualifies for any achievements and award them.
    """
    awarded = []
    
    # Get all achievements
    all_achievements = Achievement.objects.all()
    
    for achievement in all_achievements:
        # Skip if already earned
        if StudentAchievement.objects.filter(
            student=student_profile,
            achievement=achievement
        ).exists():
            continue
        
        # Check criteria
        criteria = achievement.criteria
        qualifies = False
        
        if achievement.name == "First Quiz":
            quiz_count = QuizPerformance.objects.filter(student=student_profile).count()
            if quiz_count >= 1:
                qualifies = True
        
        elif achievement.name == "Quiz Master":
            quiz_count = QuizPerformance.objects.filter(student=student_profile).count()
            if quiz_count >= 10:
                qualifies = True
        
        elif achievement.name == "Perfect Score":
            perfect_quizzes = QuizPerformance.objects.filter(
                student=student_profile,
                score=100
            ).count()
            if perfect_quizzes >= 1:
                qualifies = True
        
        elif achievement.name == "Course Completer":
            completed = CourseCompletion.objects.filter(student=student_profile).count()
            if completed >= 1:
                qualifies = True
        
        elif achievement.name == "High Achiever":
            avg_score = QuizPerformance.objects.filter(
                student=student_profile
            ).aggregate(avg=Avg('score'))['avg'] or 0
            if avg_score >= 90:
                qualifies = True
        
        elif achievement.name == "Dedicated Learner":
            total_time = QuizPerformance.objects.filter(
                student=student_profile
            ).aggregate(total=Sum('time_spent_seconds'))['total'] or 0
            if total_time >= 3600:  # 1 hour
                qualifies = True
        
        # Award achievement if qualifies
        if qualifies:
            StudentAchievement.objects.create(
                student=student_profile,
                achievement=achievement
            )
            
            # Create notification
            Notification.objects.create(
                user=student_profile.user,
                notification_type='achievement',
                title='Achievement Unlocked!',
                message=f'Congratulations! You earned the "{achievement.name}" achievement!',
                link=f'/achievements/'
            )
            
            awarded.append(achievement)
    
    return awarded

def check_course_completion(student_profile, course):
    """
    Check if student has completed all lessons and quizzes in a course.
    """
    # Get all lessons for the course
    lessons = Lesson.objects.filter(course=course)
    
    if not lessons.exists():
        return False
    
    # Check if all lessons are completed
    for lesson in lessons:
        engagement = Engagement.objects.filter(
            student=student_profile,
            lesson=lesson,
            completion_status='completed'
        ).exists()
        
        if not engagement:
            return False
        
        # Check if all quizzes for this lesson are passed
        quizzes = Quiz.objects.filter(lesson=lesson)
        for quiz in quizzes:
            quiz_performance = QuizPerformance.objects.filter(
                student=student_profile,
                quiz=quiz,
                score__gte=70  # Passing score
            ).exists()
            
            if not quiz_performance:
                return False
    
    # All lessons and quizzes completed
    return True

def mark_course_complete(student_profile, course):
    """
    Mark a course as completed and issue certificate if not already done.
    """
    completion, created = CourseCompletion.objects.get_or_create(
        student=student_profile,
        course=course
    )
    
    if created or not completion.certificate_issued:
        # Generate certificate ID
        completion.certificate_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        completion.certificate_issued = True
        completion.save()
        
        # Create notification
        Notification.objects.create(
            user=student_profile.user,
            notification_type='course_complete',
            title='Course Completed!',
            message=f'Congratulations! You completed "{course.title}"! View your certificate.',
            link=f'/course/{course.id}/certificate/'
        )
        
        # Check for achievements
        check_and_award_achievements(student_profile)
    
    return completion

