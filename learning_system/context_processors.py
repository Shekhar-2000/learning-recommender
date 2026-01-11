"""
Context processors for the learning system.
"""
from .models import Notification

def notifications(request):
    """
    Add unread notification count to all templates.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    else:
        unread_count = 0
    
    return {
        'unread_notifications_count': unread_count
    }







