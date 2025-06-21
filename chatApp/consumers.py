# chatApp/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async

from .models import ChatRoom, Message, ChatNotification
from .serializers import MessageSerializer
from userApp.models import CustomUser
from clientApp.models import Client
from professionalApp.models import Lawyer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the chat room ID from the URL
        self.chat_room_id = self.scope['url_route']['kwargs']['chat_room_id']
        self.room_group_name = f'chat_{self.chat_room_id}'
        
        # Check if user is authenticated
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Check if user has access to this chat room
        has_access = await self.check_chat_room_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user's online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope['user'].id,
                'status': 'online'
            }
        )
    
    async def disconnect(self, close_code):
        # Send user's offline status
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.scope['user'].id,
                    'status': 'offline'
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except ChatNotification.DoesNotExist:
            pass
    
    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        if not content:
            return
        
        # Save message to database
        message = await self.save_message(content)
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(message)
                }
            )
    
    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to room group (excluding sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_status',
                'user_id': self.scope['user'].id,
                'is_typing': is_typing
            }
        )
    
    async def handle_mark_read(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
    
    # WebSocket message handlers
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing_status(self, event):
        # Don't send typing status to the sender
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))
    
    async def user_status(self, event):
        # Don't send status to the user themselves
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'status': event['status']
            }))
    
    # Database operations
    @database_sync_to_async
    def check_chat_room_access(self):
        try:
            chat_room = ChatRoom.objects.get(id=self.chat_room_id)
            user = self.scope['user']
            
            if user.role == 'customer':
                client = Client.objects.get(user=user)
                return chat_room.client == client
            elif user.role == 'lawyer':
                lawyer = Lawyer.objects.get(user=user)
                return chat_room.lawyer == lawyer
            else:
                return False
        except (ChatRoom.DoesNotExist, Client.DoesNotExist, Lawyer.DoesNotExist):
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        try:
            chat_room = ChatRoom.objects.get(id=self.chat_room_id)
            message = Message.objects.create(
                chat_room=chat_room,
                sender=self.scope['user'],
                content=content,
                message_type='text'
            )
            
            # Update chat room's updated_at timestamp
            from django.utils.timezone import now
            chat_room.updated_at = now()
            chat_room.save(update_fields=['updated_at'])
            
            # Create notification for the recipient
            recipient = (
                chat_room.lawyer.user 
                if self.scope['user'].role == 'customer' 
                else chat_room.client.user
            )
            
            ChatNotification.objects.create(
                recipient=recipient,
                sender=self.scope['user'],
                chat_room=chat_room,
                notification_type='new_message',
                title=f'New message in case {chat_room.case.case_number}',
                message=f'{self.scope["user"].phone_number} sent you a message'
            )
            
            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        # Create a mock request object for serializer context
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(self.scope['user'])
        serializer = MessageSerializer(message, context={'request': mock_request})
        return serializer.data
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            # Only mark as read if the current user is not the sender
            if message.sender != self.scope['user']:
                message.mark_as_read()
        except Message.DoesNotExist:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        # Check if user is authenticated
        if self.scope['user'] == AnonymousUser():
            await self.close()
            return
        
        # Create user-specific group
        self.user_group_name = f'user_{self.scope["user"].id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_notification_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    # WebSocket message handlers
    async def notification_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = ChatNotification.objects.get(
                id=notification_id,
                recipient=self.scope['user']
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        except ChatNotification.DoesNotExist:
            pass