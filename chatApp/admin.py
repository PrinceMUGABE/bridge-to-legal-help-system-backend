# chatApp/admin.py
from django.contrib import admin
from .models import ChatRoom, Message, MessageReadStatus, ChatNotification


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'client', 'lawyer', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['case__case_number', 'client__first_name', 'client__last_name', 'lawyer__first_name', 'lawyer__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('case', 'client', 'lawyer')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_room', 'sender', 'message_type', 'content_preview', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__phone_number', 'chat_room__case__case_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('chat_room', 'sender')


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['message__content', 'user__phone_number']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'user')


@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__phone_number', 'sender__phone_number']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender', 'chat_room')