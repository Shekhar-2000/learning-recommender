from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Course, Lesson, Quiz

from rest_framework import viewsets
from .models import Course, QuizPerformance
from .serializers import CourseSerializer, QuizPerformanceSerializer

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard') # Redirect to the dashboard on successful login
    else:
        form = AuthenticationForm()
    return render(request, 'learning_system/login.html', {'form': form})

@login_required # Protect the dashboard view
def student_dashboard(request):
    courses = Course.objects.all()
    return render(request, 'learning_system/student_dashboard.html', {'courses': courses})

def user_logout(request):
    logout(request)
    return redirect('home') # Redirect to the homepage after logging out

@login_required
def student_dashboard(request):
    # ... your dashboard logic
    pass


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class QuizPerformanceViewSet(viewsets.ModelViewSet):
    queryset = QuizPerformance.objects.all()
    serializer_class = QuizPerformanceSerializer

#Example for rendering a template
def home(request):
    return render(request, 'learning_system/index.html')

# User Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login_page') # Redirect to a login page
    else:
        form = UserCreationForm()
    return render(request, 'learning_system/register.html', {'form': form})

# Basic Student Dashboard View
def student_dashboard(request):
    courses = Course.objects.all()
    return render(request, 'learning_system/student_dashboard.html', {'courses': courses})

# Quiz View
def quiz_detail(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    # You'll need to fetch questions here and pass them to the template
    if request.method == 'POST':
        # Logic to process quiz submission and save score to QuizPerformance model
        # After processing, redirect the student or show results
        pass
    return render(request, 'learning_system/quiz_page.html', {'quiz': quiz})