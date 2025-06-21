# chatApp/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import ChatNotification
from userApp.models import CustomUser


def send_notification_to_user(user_id, notification_data):
    """
    Send real-time notification to a specific user via WebSocket
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


def send_email_notification(recipient_email, subject, template_name, context):
    """
    Send email notification
    """
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def create_system_message(chat_room, content):
    """
    Create a system message in a chat room
    """
    from .models import Message
    
    # Get or create a system user (you might want to create a dedicated system user)
    try:
        system_user = CustomUser.objects.get(phone_number='system')
    except CustomUser.DoesNotExist:
        # Create system user if it doesn't exist
        system_user = CustomUser.objects.create_user(
            phone_number='system',
            role='admin',
            email='system@example.com'
        )
    
    message = Message.objects.create(
        chat_room=chat_room,
        sender=system_user,
        content=content,
        message_type='system'
    )
    
    # Send real-time update
    from .serializers import MessageSerializer
    channel_layer = get_channel_layer()
    
    # Create mock request for serializer
    class MockRequest:
        def __init__(self):
            self.user = system_user
    
    serializer = MessageSerializer(message, context={'request': MockRequest()})
    
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat_room.id}",
        {
            'type': 'chat_message',
            'message': serializer.data
        }
    )
    
    return message


def get_user_chat_stats(user):
    """
    Get chat statistics for a user
    """
    from .models import ChatRoom, Message
    from clientApp.models import Client
    from professionalApp.models import Lawyer
    
    stats = {
        'total_chat_rooms': 0,
        'active_chat_rooms': 0,
        'total_messages_sent': 0,
        'unread_messages': 0,
        'unread_notifications': 0
    }
    
    try:
        if user.role == 'customer':
            client = Client.objects.get(user=user)
            chat_rooms = ChatRoom.objects.filter(client=client)
        elif user.role == 'lawyer':
            lawyer = Lawyer.objects.get(user=user)
            chat_rooms = ChatRoom.objects.filter(lawyer=lawyer)
        else:
            return stats
        
        stats['total_chat_rooms'] = chat_rooms.count()
        stats['active_chat_rooms'] = chat_rooms.filter(is_active=True).count()
        stats['total_messages_sent'] = Message.objects.filter(
            chat_room__in=chat_rooms,
            sender=user,
            is_deleted=False
        ).count()
        stats['unread_messages'] = Message.objects.filter(
            chat_room__in=chat_rooms,
            is_deleted=False,
            is_read=False
        ).exclude(sender=user).count()
        stats['unread_notifications'] = ChatNotification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
    except Exception as e:
        print(f"Error getting chat stats: {e}")
    
    return stats


def validate_file_upload(file):
    """
    Validate file uploads for chat attachments
    """
    max_size = 10 * 1024 * 1024  # 10MB
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if file.size > max_size:
        return False, "File size too large. Maximum size is 10MB."
    
    if file.content_type not in allowed_types:
        return False, "File type not allowed."
    
    return True, "File is valid."


def format_chat_room_name(case):
    """
    Generate a formatted name for chat room
    """
    return f"Case {case.case_number} - {case.title[:30]}{'...' if len(case.title) > 30 else ''}"


def get_online_users(chat_room_id):
    """
    Get list of online users in a chat room
    This would require implementing user presence tracking
    """
    # This is a placeholder - you'd need to implement Redis-based presence tracking
    # or use Django Channels' group management features
    return []