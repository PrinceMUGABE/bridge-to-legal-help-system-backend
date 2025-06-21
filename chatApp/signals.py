# chatApp/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from caseApp.models import Case
from .models import ChatRoom, ChatNotification


@receiver(post_save, sender=Case)
def create_chat_room_on_case_assignment(sender, instance, created, **kwargs):
    """
    Automatically create a chat room when a case is assigned to a lawyer
    """
    if not created and instance.lawyer and instance.status == 'assigned':
        # Check if chat room already exists
        if not hasattr(instance, 'chat_room'):
            # Create chat room
            chat_room = ChatRoom.objects.create(
                case=instance,
                client=instance.client,
                lawyer=instance.lawyer
            )
            
            # Create notifications for both parties
            ChatNotification.objects.create(
                recipient=instance.client.user,
                chat_room=chat_room,
                notification_type='case_assigned',
                title=f'Chat room created for case {instance.case_number}',
                message=f'You can now chat with your assigned lawyer'
            )
            
            ChatNotification.objects.create(
                recipient=instance.lawyer.user,
                chat_room=chat_room,
                notification_type='case_assigned',
                title=f'Chat room created for case {instance.case_number}',
                message=f'You can now chat with your client'
            )


@receiver(post_save, sender=Case)
def notify_case_status_change(sender, instance, created, **kwargs):
    """
    Send notification when case status changes
    """
    if not created and hasattr(instance, 'chat_room'):
        chat_room = instance.chat_room
        
        # Create notifications for both parties about status change
        status_display = dict(Case.STATUS_CHOICES).get(instance.status, instance.status)
        
        ChatNotification.objects.create(
            recipient=instance.client.user,
            chat_room=chat_room,
            notification_type='case_status_changed',
            title=f'Case {instance.case_number} status updated',
            message=f'Your case status has been changed to: {status_display}'
        )
        
        if instance.lawyer:
            ChatNotification.objects.create(
                recipient=instance.lawyer.user,
                chat_room=chat_room,
                notification_type='case_status_changed',
                title=f'Case {instance.case_number} status updated',
                message=f'Case status has been changed to: {status_display}'
            )


@receiver(post_save, sender=ChatNotification)
def send_realtime_notification(sender, instance, created, **kwargs):
    """
    Send real-time notification via WebSocket when a new notification is created
    """
    if created:
        channel_layer = get_channel_layer()
        
        # Send to user's notification channel
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.recipient.id}",
            {
                'type': 'notification_message',
                'notification': {
                    'id': instance.id,
                    'title': instance.title,
                    'message': instance.message,
                    'notification_type': instance.notification_type,
                    'created_at': instance.created_at.isoformat(),
                    'case_number': instance.chat_room.case.case_number if instance.chat_room else None,
                    'sender': {
                        'id': instance.sender.id,
                        'phone_number': instance.sender.phone_number
                    } if instance.sender else None
                }
            }
        )