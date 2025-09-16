"""
URL configuration for core_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, QuizPerformanceViewSet
from . import views  # Import your views



router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'quiz-performance', QuizPerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    #path('api/', include(router.urls)), # Your API URLs
]