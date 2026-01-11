import os
import django

# Ensure this matches your project settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_app.settings')

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "admin"
email = "admin@example.com"
password = "AdminPass123!"

u = User.objects.filter(username=username).first()
if u:
    u.set_password(password)
    u.email = email
    u.save()
    print(f"Updated superuser: {username}")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Created superuser: {username}")
