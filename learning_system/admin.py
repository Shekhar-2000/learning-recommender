from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

# Register your models here.

from .models import CustomUser
from .models import Course, Quiz, QuizPerformance
from django.contrib.auth.admin import UserAdmin


def users_table_view(request):
	"""Admin-protected view that displays a paginated table of all users.

	Supports:
	- ?q=search_term (search in username or email)
	- ?role=student|teacher|staff|superuser|active (filter by role)
	- ?export=csv (download the current filtered set as CSV)
	- pagination with ?page=
	"""
	qs = CustomUser.objects.all().order_by('-date_joined')

	# filters
	q = request.GET.get('q')
	if q:
		qs = qs.filter(models.Q(username__icontains=q) | models.Q(email__icontains=q))

	role = request.GET.get('role')
	if role == 'student':
		qs = qs.filter(is_student=True)
	elif role == 'teacher':
		qs = qs.filter(is_teacher=True)
	elif role == 'staff':
		qs = qs.filter(is_staff=True)
	elif role == 'superuser':
		qs = qs.filter(is_superuser=True)
	elif role == 'active':
		qs = qs.filter(is_active=True)

	# Export CSV if requested (no pagination for export)
	if request.GET.get('export') == 'csv':
		resp = HttpResponse(content_type='text/csv')
		resp['Content-Disposition'] = 'attachment; filename="users_export.csv"'
		writer = csv.writer(resp)
		writer.writerow(['id', 'username', 'email', 'is_staff', 'is_superuser', 'is_student', 'is_teacher', 'is_active', 'date_joined'])
		for u in qs:
			writer.writerow([u.id, u.username, u.email, u.is_staff, u.is_superuser, u.is_student, u.is_teacher, u.is_active, u.date_joined])
		return resp

	# KPIs
	total_users = CustomUser.objects.count()
	total_students = CustomUser.objects.filter(is_student=True).count()
	total_teachers = CustomUser.objects.filter(is_teacher=True).count()
	total_active = CustomUser.objects.filter(is_active=True).count()

	paginator = Paginator(qs, 25)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	context = {
		**admin.site.each_context(request),
		'users_page': page_obj,
		'total_users': total_users,
		'total_students': total_students,
		'total_teachers': total_teachers,
		'total_active': total_active,
		'search_q': q or '',
		'filter_role': role or '',
	}
	return render(request, 'admin/users_table.html', context)


# Hook the view into the admin URL patterns so it's available at /admin/users-table/

# FAQ chatbot view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import re

FAQ_ANSWERS = {
	r"how (do|can) i add a course": "Go to 'Manage Courses' in the admin dashboard and click 'Add Course'.",
	r"how (do|can) i add a user": "Go to 'View Users Table' and click 'Add user' or use the Django admin Users page.",
	r"how (do|can) i export users": "Use the 'Export CSV' button in the Users Table page.",
	r"how (do|can) i see recent users": "Check the Users Table for the latest users sorted by join date.",
	r"how (do|can) i view quizzes": "Go to 'Manage Quizzes' in the admin dashboard.",
	r"how (do|can) i reset a password": "Use the Django admin Users page to change or reset passwords.",
	r"how (do|can) i see analytics": "Analytics widgets and charts are available on the admin dashboard.",
	r"how (do|can) i register": "Click 'Register' on the login page and fill out the form to create a new account.",
	r"how (do|can) i login": "Go to the login page and enter your username and password.",
	r"how (do|can) i logout": "Click the 'Logout' button in the navigation bar to log out.",
	r"how (do|can) i view my dashboard": "After logging in, you'll be redirected to your dashboard based on your role.",
	r"how (do|can) i view my progress": "Your dashboard shows your learning progress, completed quizzes, and average score.",
	r"how (do|can) i view available courses": "Courses are listed in your dashboard. Click 'View Course' for details.",
	r"how (do|can) i take a quiz": "Open a course, select a lesson, and click on the quiz to start.",
	r"how (do|can) i get recommendations": "Complete the initial assessment to receive personalized course recommendations.",
	r"how (do|can) i contact support": "Use the FAQ chatbot or contact your teacher/admin for help.",
	r"how (do|can) i view student progress": "Teachers can view student progress in the Teacher Dashboard under 'Student Management'.",
	r"how (do|can) i manage my profile": "Go to 'Settings' in your dashboard to update your profile and preferences.",
	r"how (do|can) i view certificates": "Certificates and achievements are shown in your dashboard under 'Certificates'.",
	r"how (do|can) i add a lesson": "Go to 'Manage Courses', select a course, and add a lesson from the course detail page.",
	r"how (do|can) i add a question": "Go to 'Manage Quizzes', select a quiz, and add questions from the quiz detail page.",
	r"how (do|can) i view engagement": "Engagement stats are shown in the dashboard analytics section.",
	r"how (do|can) i view errors": "If you see an error, check the FAQ or contact your admin for help.",
	r"how (do|can) i view recommendations": "Recommendations are shown on your dashboard after completing the assessment.",
	r"what is the site about": "This platform helps students learn, take quizzes, and get personalized course recommendations.",
	r"what is a dashboard": "A dashboard is your main page showing your progress, courses, and quick actions.",
	r"what is a quiz": "A quiz tests your knowledge on a lesson. Complete quizzes to track your learning progress.",
	r"what is a course": "A course is a collection of lessons and quizzes on a specific topic.",
	r"what is a lesson": "A lesson is a unit of learning within a course, often followed by a quiz.",
	r"what is engagement": "Engagement measures your activity and time spent learning on the platform.",
	r"what is a recommendation": "Recommendations suggest courses based on your assessment and learning profile."
}

@csrf_exempt
def faq_chatbot_view(request):
	if request.method == 'POST':
		question = request.POST.get('message', '').lower().strip()
		for pattern, answer in FAQ_ANSWERS.items():
			if re.search(pattern, question):
				return JsonResponse({'answer': answer})
		# Fallback: list supported topics
		topics = [
			"courses", "users", "quizzes", "dashboard", "registration", "progress", "recommendations", "analytics", "profile", "lessons", "engagement", "certificates", "errors", "support"
		]
		return JsonResponse({'answer': "Sorry, I don't know the answer to that. Supported topics: " + ', '.join(topics) + ". Try asking about one of these."})
	return JsonResponse({'error': 'Only POST allowed'}, status=405)

_original_get_urls = admin.site.get_urls

def get_urls():
	urls = _original_get_urls()
	my_urls = [
		path('users-table/', admin.site.admin_view(users_table_view), name='users_table'),
		path('faq-chatbot/', faq_chatbot_view, name='faq_chatbot'),
	]
	return my_urls + urls

admin.site.get_urls = get_urls

# Use a custom index template so we can add a prominent link to the users table
admin.site.index_template = 'admin/custom_index.html'


# Register key models so their admin changelist URL names exist and the links in the
# custom index template resolve correctly.
try:
	admin.site.register(Course)
except Exception:
	# If already registered, skip
	pass

try:
	admin.site.register(Quiz)
except Exception:
	pass

try:
	admin.site.register(QuizPerformance)
except Exception:
	pass

# Register CustomUser with the standard UserAdmin for sensible defaults
try:
	admin.site.register(CustomUser, UserAdmin)
except Exception:
	# If CustomUser was already registered elsewhere, ignore
	pass
