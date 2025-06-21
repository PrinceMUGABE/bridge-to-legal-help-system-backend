# chatApp/models.py
from django.db import models
from django.utils.timezone import now
from userApp.models import CustomUser
from caseApp.models import Case
from clientApp.models import Client
from professionalApp.models import Lawyer


class ChatRoom(models.Model):
    """
    Chat room for a specific case between client and lawyer
    """
    case = models.OneToOneField(
        Case,
        on_delete=models.CASCADE,
        related_name='chat_room'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )
    lawyer = models.ForeignKey(
        Lawyer,
        on_delete=models.CASCADE,
        related_name='chat_rooms'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'
    
    def __str__(self):
        return f"Chat Room - Case: {self.case.case_number}"
    
    @property
    def room_name(self):
        """Generate unique room name for WebSocket"""
        return f"case_{self.case.id}"
    
    def get_participants(self):
        """Get all participants in the chat room"""
        return [self.client.user, self.lawyer.user]


class Message(models.Model):
    """
    Individual messages in chat rooms
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('system', 'System'),
    ]
    
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    
    # Message status
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"Message from {self.sender.phone_number} in {self.chat_room.case.case_number}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageReadStatus(models.Model):
    """
    Track read status of messages by users
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='message_read_statuses'
    )
    read_at = models.DateTimeField(default=now)
    
    class Meta:
        unique_together = ['message', 'user']
        verbose_name = 'Message Read Status'
        verbose_name_plural = 'Message Read Statuses'
    
    def __str__(self):
        return f"{self.user.phone_number} read message at {self.read_at}"


class ChatNotification(models.Model):
    """
    Notifications for chat events
    """
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('case_assigned', 'Case Assigned'),
        ('case_status_changed', 'Case Status Changed'),
    ]
    
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_notifications'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_chat_notifications',
        null=True,
        blank=True
    )
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat Notification'
        verbose_name_plural = 'Chat Notifications'
    
    def __str__(self):
        return f"Notification for {self.recipient.phone_number}: {self.title}"