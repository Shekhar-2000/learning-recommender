from django.db import models
from django.contrib.auth.models import User

# Extends the default Django User model for student-specific info
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add other fields like learning_style, grade_level, etc.
    # learning_style = models.CharField(max_length=50)

# Teacher Profile
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add teacher-specific fields

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()

class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.TextField()

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

# Tracks student quiz scores and attempts
class QuizPerformance(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    time_spent_seconds = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

# Tracks student engagement with lessons (e.g., video views, time spent)
class Engagement(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    time_spent_seconds = models.IntegerField()
    completion_status = models.CharField(max_length=20, default='in_progress')
    timestamp = models.DateTimeField(auto_now_add=True)
