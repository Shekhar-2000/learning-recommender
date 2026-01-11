from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from rest_framework import viewsets
from django.views.decorators.http import require_POST
import json
from .serializers import CourseSerializer, QuizPerformanceSerializer
from .models import (
    Course,
    Quiz,
    Question,
    Answer,
    QuizPerformance,
    StudentProfile,
    TeacherProfile,
    Engagement,
    AssessmentQuiz,
    AssessmentQuestion,
    AssessmentAnswer,
    AssessmentResult,
    ChatGroup,
    GroupChatMessage,
    CourseBookmark,
    CourseRating,
    CourseCompletion,
    Achievement,
    StudentAchievement,
    Notification,
)
from .forms import ChatGroupCreationForm, CustomUserCreationForm
from .recommender import AdvancedRecommender


# ------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------

def _get_or_create_student_profile(user):
    """Helper function to get or create a student profile."""
    return StudentProfile.objects.get_or_create(user=user)


def _enrich_courses_for_display(courses):
    """
    Attach rating and tag metadata expected by templates.
    """
    for course in courses:
        rating_stats = course.ratings.aggregate(
            avg_rating=Avg('rating'),
            rating_count=Count('id')
        )
        avg_rating = rating_stats['avg_rating'] or 0
        course.avg_rating = round(avg_rating, 1) if avg_rating else 0
        course.rating_count = rating_stats['rating_count']
        if course.tags:
            course.tags_list = [tag.strip() for tag in course.tags.split(',') if tag.strip()]
        else:
            course.tags_list = []
    return courses


# ------------------------------------------------------------------
# GROUP CHAT CREATION VIEW
# ------------------------------------------------------------------
@login_required
def create_chat_group(request):
    if request.method == 'POST':
        form = ChatGroupCreationForm(request.POST)
        if form.is_valid():
            group = form.save()
            group.members.add(request.user)  # Add creator to group
            return redirect('chat_group_detail', group_id=group.id)
    else:
        form = ChatGroupCreationForm()
    return render(request, 'learning_system/create_chat_group.html', {'form': form})


@login_required
def chat_group_detail(request, group_id):
    """
    Displays the details of a chat group including members and messages.
    """
    group = get_object_or_404(ChatGroup, id=group_id)
    
    # Check if user is a member of the group
    if request.user not in group.members.all():
        return HttpResponseForbidden("You are not a member of this chat group.")
    
    # Get all messages for this group, ordered by timestamp
    messages = GroupChatMessage.objects.filter(group=group).order_by('timestamp')
    
    return render(request, 'learning_system/chat_group_detail.html', {
        'group': group,
        'messages': messages
    })

# ------------------------------------------------------------------
# AUTHENTICATION & CORE VIEWS
# ------------------------------------------------------------------

def home(request):
    """
    Renders the homepage.
    """
    return render(request, 'learning_system/index.html')

def register(request):
    """
    Handles user registration for both students and teachers.
    Creates a user account and an associated profile.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_teacher = form.cleaned_data.get('is_teacher', False)
            user.is_student = not user.is_teacher
            user.save()

            # Create a profile based on the user's role
            if user.is_student:
                StudentProfile.objects.create(user=user)
            elif user.is_teacher:
                TeacherProfile.objects.create(user=user)

            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'learning_system/register.html', {'form': form})


def user_login(request):
    """
    Handles user login.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to the correct dashboard based on role
                if user.is_teacher:
                    return redirect('teacher_dashboard')
                else:
                    return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'learning_system/login.html', {'form': form})


def user_logout(request):
    """
    Handles user logout.
    """
    logout(request)
    return redirect('home')

# ------------------------------------------------------------------
# DASHBOARD & LEARNING VIEWS
# ------------------------------------------------------------------

@login_required
def student_dashboard(request):
    """
    Displays the main dashboard for students with personalized course recommendations.
    """
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        # Option 1: Create profile automatically
        student_profile = StudentProfile.objects.create(user=request.user)
        # Option 2: Show friendly error (uncomment if you prefer)
        # return render(request, 'learning_system/student_dashboard.html', {
        #     'error': 'No student profile found. Please contact support.'
        # })
    
    # Check if student has completed initial assessment
    assessment_result = AssessmentResult.objects.filter(student=student_profile).first()
    
    # Get advanced recommendations
    recommender = AdvancedRecommender()
    
    if assessment_result:
        # Use hybrid recommendations combining all methods
        courses = recommender.get_hybrid_recommendations(student_profile, n_recommendations=8)
        
        # If no recommendations, fall back to assessment-based recommendations
        if not courses:
            recommended_course_ids = assessment_result.recommended_courses
            courses = Course.objects.filter(id__in=recommended_course_ids)
            if not courses.exists():
                courses = Course.objects.all()[:8]
    else:
        # No assessment completed, show all courses
        courses = Course.objects.all()[:8]
    
    # Get student statistics
    quiz_performances = QuizPerformance.objects.filter(student=student_profile)
    total_quizzes = quiz_performances.count()
    completed_quizzes = quiz_performances.filter(score__gte=70).count()
    avg_score = quiz_performances.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    
    # Calculate total learning time
    total_time_seconds = quiz_performances.aggregate(total_time=Sum('time_spent_seconds'))['total_time'] or 0
    total_time_hours = total_time_seconds / 3600
    
    return render(request, 'learning_system/student_dashboard.html', {
        'courses': courses,
        'has_assessment': assessment_result is not None,
        'learning_level': assessment_result.learning_level if assessment_result else 'beginner',
        'total_quizzes': total_quizzes,
        'completed_quizzes': completed_quizzes,
        'avg_score': round(avg_score, 1),
        'total_time_hours': round(total_time_hours, 1)
    })


@login_required
def my_bookmarks(request):
    """
    Displays all bookmarked courses for the current student.
    """
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can view bookmarks.")
    
    student_profile, _ = _get_or_create_student_profile(request.user)
    bookmark_entries = CourseBookmark.objects.filter(student=student_profile).select_related('course')
    courses = _enrich_courses_for_display([b.course for b in bookmark_entries])
    
    return render(request, 'learning_system/my_bookmarks.html', {
        'courses': courses
    })


@login_required
@require_POST
def toggle_bookmark(request, course_id):
    """
    Toggle bookmark status for a course.
    """
    if not request.user.is_student:
        return JsonResponse({'success': False, 'message': 'Only students can bookmark courses.'}, status=403)
    
    student_profile, _ = _get_or_create_student_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    bookmark, created = CourseBookmark.objects.get_or_create(
        student=student_profile,
        course=course
    )
    
    if created:
        message = 'Course bookmarked!'
        status = 'added'
    else:
        bookmark.delete()
        message = 'Bookmark removed.'
        status = 'removed'
    
    return JsonResponse({'success': True, 'status': status, 'message': message})


@login_required
def my_achievements(request):
    """
    Displays all achievements for the current student.
    """
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can view achievements.")
    
    student_profile, _ = _get_or_create_student_profile(request.user)
    all_achievements = Achievement.objects.all()
    earned_achievements = StudentAchievement.objects.filter(
        student=student_profile
    ).select_related('achievement')
    
    total_count = all_achievements.count()
    earned_count = earned_achievements.count()
    completion_percentage = round((earned_count / total_count * 100) if total_count > 0 else 0, 1)
    earned_ids = set(earned_achievements.values_list('achievement_id', flat=True))
    
    return render(request, 'learning_system/my_achievements.html', {
        'earned_achievements': earned_achievements,
        'all_achievements': all_achievements,
        'earned_count': earned_count,
        'total_count': total_count,
        'completion_percentage': completion_percentage,
        'earned_ids': earned_ids
    })


@login_required
def progress_analytics(request):
    """
    Displays learning progress analytics for the current student.
    """
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can view analytics.")
    
    student_profile, _ = _get_or_create_student_profile(request.user)
    quiz_performances = QuizPerformance.objects.filter(student=student_profile).order_by('-timestamp')
    
    total_quizzes = quiz_performances.count()
    avg_score = quiz_performances.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    total_time_seconds = quiz_performances.aggregate(total_time=Sum('time_spent_seconds'))['total_time'] or 0
    total_time_hours = total_time_seconds / 3600
    completed_courses = CourseCompletion.objects.filter(student=student_profile).count()
    
    score_data = [
        {
            'date': qp.timestamp.strftime('%b %d'),
            'score': qp.score
        }
        for qp in quiz_performances.order_by('timestamp')
    ]
    
    return render(request, 'learning_system/progress_analytics.html', {
        'total_quizzes': total_quizzes,
        'avg_score': round(avg_score, 1),
        'total_time_hours': round(total_time_hours, 1),
        'completed_courses': completed_courses,
        'quiz_performances': quiz_performances[:10],
        'score_data': json.dumps(score_data),
    })


def search_courses(request):
    """
    Search for courses by title, description, or tags.
    """
    query = request.GET.get('q', '').strip()
    courses = Course.objects.all()
    
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
    
    courses = courses.annotate(
        avg_rating=Avg('ratings__rating'),
        rating_count=Count('ratings', distinct=True)
    )
    
    return render(request, 'learning_system/search_results.html', {
        'query': query,
        'courses': courses
    })


@login_required
def notifications_view(request):
    """
    Displays all notifications for the current user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'learning_system/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return JsonResponse({'success': True})


@login_required
def teacher_dashboard(request):
    """
    Displays the main dashboard for teachers, showing a list of students and analytics.
    """
    # Security check: only teachers can access this page
    if not request.user.is_teacher:
        return HttpResponseForbidden("You are not authorized to view this page.")

    students = StudentProfile.objects.all()
    
    # Get analytics data
    total_students = students.count()
    total_courses = Course.objects.count()
    total_quizzes = Quiz.objects.count()
    
    # Get performance statistics
    quiz_performances = QuizPerformance.objects.all()
    avg_performance = quiz_performances.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    total_attempts = quiz_performances.count()
    
    # Get engagement statistics
    engagements = Engagement.objects.all()
    total_engagement_time = engagements.aggregate(total_time=Sum('time_spent_seconds'))['total_time'] or 0
    total_engagement_hours = total_engagement_time / 3600
    
    # Get student progress data
    student_progress = []
    for student in students:
        student_quizzes = QuizPerformance.objects.filter(student=student)
        student_avg = student_quizzes.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        student_completed = student_quizzes.filter(score__gte=70).count()
        student_total = student_quizzes.count()
        
        student_progress.append({
            'student': student,
            'avg_score': round(student_avg, 1),
            'completed_quizzes': student_completed,
            'total_quizzes': student_total,
            'completion_rate': round((student_completed / student_total * 100) if student_total > 0 else 0, 1)
        })
    
    # Sort by completion rate
    student_progress.sort(key=lambda x: x['completion_rate'], reverse=True)
    
    return render(request, 'learning_system/teacher_dashboard.html', {
        'students': students,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_quizzes': total_quizzes,
        'avg_performance': round(avg_performance, 1),
        'total_attempts': total_attempts,
        'total_engagement_hours': round(total_engagement_hours, 1),
        'student_progress': student_progress
    })

@login_required
def course_detail(request, course_id):
    """
    Displays the details for a single course, including its lessons and quizzes.
    """
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'learning_system/course_detail.html', {'course': course})

@login_required
def quiz_detail(request, quiz_id):
    """
    Displays a quiz and handles the submission of answers.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.question_set.all()

    if request.method == 'POST':
        score = 0
        total_questions = questions.count()

        if total_questions > 0:
            for question in questions:
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        answer = Answer.objects.get(id=answer_id)
                        if answer.is_correct:
                            score += 1
                    except Answer.DoesNotExist:
                        continue # Ignore if the answer ID is invalid
            
            # Calculate score as a percentage
            final_score = (score / total_questions) * 100
        else:
            final_score = 100 # Or 0, depending on how you want to handle empty quizzes

        student_profile = StudentProfile.objects.get(user=request.user)

        # Save the quiz performance
        QuizPerformance.objects.create(
            student=student_profile,
            quiz=quiz,
            score=final_score,
            time_spent_seconds=60  # Placeholder, you'll need to implement a timer
        )
        return redirect('dashboard')

    return render(request, 'learning_system/quiz_page.html', {'quiz': quiz, 'questions': questions})

# ------------------------------------------------------------------
# ASSESSMENT VIEWS
# ------------------------------------------------------------------

@login_required
def initial_assessment(request):
    """
    Displays the initial assessment quiz for new students.
    """
    student_profile = StudentProfile.objects.get(user=request.user)
    
    # Check if student already completed assessment
    if AssessmentResult.objects.filter(student=student_profile).exists():
        return redirect('dashboard')
    
    assessment = AssessmentQuiz.objects.filter(is_active=True).first()
    if not assessment:
        return redirect('dashboard')
    
    questions = assessment.assessmentquestion_set.all()
    
    if request.method == 'POST':
        # Process assessment answers
        skill_scores = {}
        total_score = 0
        
        for question in questions:
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    answer = AssessmentAnswer.objects.get(id=answer_id)
                    # Add skill points
                    for skill, points in answer.skill_points.items():
                        skill_scores[skill] = skill_scores.get(skill, 0) + points
                    total_score += sum(answer.skill_points.values())
                except AssessmentAnswer.DoesNotExist:
                    continue
        
        # Determine learning level
        if total_score >= 80:
            learning_level = 'advanced'
        elif total_score >= 50:
            learning_level = 'intermediate'
        else:
            learning_level = 'beginner'
        
        # Generate course recommendations based on skill scores
        recommended_courses = get_course_recommendations(skill_scores, learning_level)
        
        # Save assessment result
        AssessmentResult.objects.create(
            student=student_profile,
            assessment=assessment,
            total_score=total_score,
            skill_scores=skill_scores,
            recommended_courses=recommended_courses,
            learning_level=learning_level
        )
        
        return redirect('dashboard')
    
    return render(request, 'learning_system/initial_assessment.html', {
        'assessment': assessment,
        'questions': questions
    })

def get_course_recommendations(skill_scores, learning_level):
    """
    Generate course recommendations based on assessment results.
    """
    recommended_courses = []
    
    # Get all courses
    all_courses = Course.objects.all()
    
    # Simple recommendation logic based on skill scores
    for course in all_courses:
        course_score = 0
        
        # Check course tags against skills
        if course.tags:
            tags = course.tags.lower()
            for skill, score in skill_scores.items():
                if skill.lower() in tags:
                    course_score += score
        
        # Add courses with positive scores or if no specific skills match
        if course_score > 0 or not skill_scores:
            recommended_courses.append(course.id)
    
    # If no recommendations, return all courses
    if not recommended_courses:
        recommended_courses = list(all_courses.values_list('id', flat=True))
    
    return recommended_courses

# ------------------------------------------------------------------
# API VIEWS (for REST Framework)
# ------------------------------------------------------------------

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class QuizPerformanceViewSet(viewsets.ModelViewSet):
    queryset = QuizPerformance.objects.all()
    serializer_class = QuizPerformanceSerializer

@login_required
def get_recommendations_api(request):
    """
    API endpoint to get personalized recommendations for a student.
    """
    if not request.user.is_student:
        return JsonResponse({'error': 'Only students can access recommendations'}, status=403)
    
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        recommender = AdvancedRecommender()
        
        # Get different types of recommendations
        hybrid_recs = recommender.get_hybrid_recommendations(student_profile, n_recommendations=5)
        collab_recs = recommender.get_collaborative_recommendations(student_profile, n_recommendations=3)
        content_recs = recommender.get_content_based_recommendations(student_profile, n_recommendations=3)
        kg_recs = recommender.get_knowledge_graph_recommendations(student_profile, n_recommendations=3)
        
        # Serialize recommendations
        recommendations = {
            'hybrid': [
                {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'tags': course.tags.split(',') if course.tags else []
                } for course in hybrid_recs
            ],
            'collaborative': [
                {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'tags': course.tags.split(',') if course.tags else []
                } for course in collab_recs
            ],
            'content_based': [
                {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'tags': course.tags.split(',') if course.tags else []
                } for course in content_recs
            ],
            'knowledge_graph': [
                {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'tags': course.tags.split(',') if course.tags else []
                } for course in kg_recs
            ]
        }
        
        return JsonResponse({
            'success': True,
            'recommendations': recommendations,
            'timestamp': timezone.now().isoformat()
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
