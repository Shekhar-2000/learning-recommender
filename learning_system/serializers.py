from rest_framework import serializers
from .models import Course, QuizPerformance

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class QuizPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizPerformance
        fields = '__all__'