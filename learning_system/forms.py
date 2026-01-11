from django import forms
from django.contrib.auth.forms import UserCreationForm
# Make sure you are importing your CustomUser model
from .models import CustomUser 

class CustomUserCreationForm(UserCreationForm):
    # These fields are added to the default registration form
    is_teacher = forms.BooleanField(required=False, label="Register as a teacher")
    is_student = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput())


    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('is_teacher',)


# Group chat creation form
from .models import ChatGroup
from django.conf import settings
from .models import CustomUser
class ChatGroupCreationForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.all(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = ChatGroup
        fields = ['name', 'members']