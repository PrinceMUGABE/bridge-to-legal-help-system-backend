# chatApp/serializers.py
from rest_framework import serializers
from django.utils.timezone import now
from .models import ChatRoom, Message, MessageReadStatus, ChatNotification
from userApp.models import CustomUser
from caseApp.models import Case


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for chat"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'full_name']
    
    def get_full_name(self, obj):
        if hasattr(obj, 'client'):
            return f"{obj.client.first_name} {obj.client.last_name}"
        elif hasattr(obj, 'lawyer'):
            return f"{obj.lawyer.first_name} {obj.lawyer.last_name}"
        return obj.phone_number


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    is_own_message = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content', 'attachment',
            'is_read', 'created_at', 'updated_at', 'is_own_message',
            'formatted_time'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at', 'is_read']
    
    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender == request.user
        return False
    
    def get_formatted_time(self, obj):
        return obj.created_at.strftime('%H:%M')


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_type', 'content', 'attachment']
    
    def create(self, validated_data):
        chat_room = self.context.get('chat_room')
        if not chat_room:
            raise serializers.ValidationError("Chat room not found in context")
            
        sender = self.context['request'].user
        
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            **validated_data
        )
        
        # Update chat room's updated_at timestamp
        chat_room.updated_at = now()
        chat_room.save(update_fields=['updated_at'])
        
        return message

class ChatRoomSerializer(serializers.ModelSerializer):
    case_title = serializers.CharField(source='case.title', read_only=True)
    case_number = serializers.CharField(source='case.case_number', read_only=True)
    case_status = serializers.CharField(source='case.status', read_only=True)
    client = UserBasicSerializer(source='client.user', read_only=True)
    lawyer = UserBasicSerializer(source='lawyer.user', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'case_title', 'case_number', 'case_status',
            'client', 'lawyer', 'is_active', 'created_at',
            'updated_at', 'last_message', 'unread_count'
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages.filter(is_deleted=False).last()
        if last_message:
            return {
                'content': last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                'sender': last_message.sender.phone_number,
                'created_at': last_message.created_at,
                'message_type': last_message.message_type
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(
                is_deleted=False,
                is_read=False
            ).exclude(sender=request.user).count()
        return 0


class ChatNotificationSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    case_number = serializers.CharField(source='chat_room.case.case_number', read_only=True)
    
    class Meta:
        model = ChatNotification
        fields = [
            'id', 'sender', 'notification_type', 'title', 'message',
            'is_read', 'created_at', 'case_number'
        ]