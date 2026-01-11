from django.db import models
from django.conf import settings
# ------------------------------------------------------------------
# 5. GROUP CHAT MODELS
# ------------------------------------------------------------------
class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupChatMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.message[:30]}..."

from django.contrib.auth.models import AbstractUser

# ------------------------------------------------------------------
# 1. USER AND PROFILE MODELS
# ------------------------------------------------------------------

class CustomUser(AbstractUser):
    """
    This is your single, custom user model for the entire application.
    """
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

class StudentProfile(models.Model):
    """
    Links a student user to their specific profile.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

class TeacherProfile(models.Model):
    """
    Links a teacher user to their specific profile.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)


# ------------------------------------------------------------------
# 2. COURSE CONTENT MODELS
# ------------------------------------------------------------------

class Course(models.Model):
    """
    Represents a course, like 'AI/ML' or 'Web Development'.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

class Lesson(models.Model):
    """
    Represents a single lesson within a course.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()

class Quiz(models.Model):
    """
    Represents a quiz that belongs to a single lesson.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

class Question(models.Model):
    """
    A single question within a quiz.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.TextField()

class Answer(models.Model):
    """
    A possible answer to a question. Can be correct or incorrect.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)


# ------------------------------------------------------------------
# 3. USER ACTIVITY AND PERFORMANCE MODELS
# ------------------------------------------------------------------

class QuizPerformance(models.Model):
    """
    Tracks a student's score and time on a specific quiz attempt.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    time_spent_seconds = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Engagement(models.Model):
    """
    Tracks a student's interaction with a lesson.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    time_spent_seconds = models.IntegerField()
    completion_status = models.CharField(max_length=20, default='in_progress')
    timestamp = models.DateTimeField(auto_now_add=True)

class AssessmentQuiz(models.Model):
    """
    Initial assessment quiz for new students to determine their learning level and preferences.
    """
    title = models.CharField(max_length=200, default="Initial Learning Assessment")
    description = models.TextField(default="Complete this assessment to get personalized course recommendations.")
    is_active = models.BooleanField(default=True)

class AssessmentQuestion(models.Model):
    """
    Questions for the initial assessment quiz.
    """
    assessment = models.ForeignKey(AssessmentQuiz, on_delete=models.CASCADE)
    text = models.TextField()
    category = models.CharField(max_length=50)  # e.g., 'programming', 'math', 'logic', 'preference'
    difficulty_level = models.IntegerField(default=1)  # 1-5 scale
    question_type = models.CharField(max_length=20, default='multiple_choice')

class AssessmentAnswer(models.Model):
    """
    Possible answers for assessment questions.
    """
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    skill_points = models.JSONField(default=dict)  # Points awarded for different skills

class AssessmentResult(models.Model):
    """
    Stores the results of a student's initial assessment.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    assessment = models.ForeignKey(AssessmentQuiz, on_delete=models.CASCADE)
    total_score = models.IntegerField()
    skill_scores = models.JSONField(default=dict)  # Breakdown by skill/category
    recommended_courses = models.JSONField(default=list)  # Course IDs
    learning_level = models.CharField(max_length=20, default='beginner')  # beginner, intermediate, advanced

    timestamp = models.DateTimeField(auto_now_add=True)

# ------------------------------------------------------------------
# 4. SUPPORT CHAT MODELS
# ------------------------------------------------------------------
from django.conf import settings
class SupportChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.message[:30]}..."

# ------------------------------------------------------------------
# 6. ACHIEVEMENTS AND NOTIFICATIONS
# ------------------------------------------------------------------

class Achievement(models.Model):
    """
    Represents an achievement that students can earn.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-trophy')
    criteria = models.JSONField(default=dict)
    points = models.IntegerField(default=10)

    def __str__(self):
        return self.name


class StudentAchievement(models.Model):
    """
    Links a student to an achievement they've earned.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'achievement')

    def __str__(self):
        return f"{self.student.user.username} - {self.achievement.name}"


class Notification(models.Model):
    """
    Notifications for users about achievements, course completions, etc.
    """
    NOTIFICATION_TYPES = [
        ('achievement', 'Achievement Earned'),
        ('course_complete', 'Course Completed'),
        ('new_course', 'New Course Available'),
        ('quiz_reminder', 'Quiz Reminder'),
        ('message', 'New Message'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


# ------------------------------------------------------------------
# 7. COURSE INTERACTIONS
# ------------------------------------------------------------------

class CourseBookmark(models.Model):
    """
    Allows students to bookmark courses for later.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='bookmarks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} bookmarked {self.course.title}"


class CourseRating(models.Model):
    """
    Allows students to rate courses.
    """
    RATING_CHOICES = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.user.username} rated {self.course.title} - {self.rating} stars"


class CourseCompletion(models.Model):
    """
    Tracks when a student completes a course.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='completed_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} completed {self.course.title}"