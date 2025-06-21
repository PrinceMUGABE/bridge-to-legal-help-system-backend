# chatApp/views.py
from urllib import request
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils.timezone import now
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


from .models import ChatRoom, Message, ChatNotification
from .serializers import (
    ChatRoomSerializer, MessageSerializer, MessageCreateSerializer,
    ChatNotificationSerializer
)
from caseApp.models import Case
from clientApp.models import Client
from professionalApp.models import Lawyer
from rest_framework.exceptions import PermissionDenied


class ChatRoomListView(generics.ListAPIView):
    """List all chat rooms for the authenticated user"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'customer':
            # Get chat rooms where user is the client
            client = get_object_or_404(Client, user=user)
            return ChatRoom.objects.filter(client=client, is_active=True)
        elif user.role == 'lawyer':
            # Get chat rooms where user is the lawyer
            lawyer = get_object_or_404(Lawyer, user=user)
            return ChatRoom.objects.filter(lawyer=lawyer, is_active=True)
        else:
            return ChatRoom.objects.none()


class ChatRoomDetailView(generics.RetrieveAPIView):
    """Get details of a specific chat room"""
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'customer':
            client = get_object_or_404(Client, user=user)
            return ChatRoom.objects.filter(client=client, is_active=True)
        elif user.role == 'lawyer':
            lawyer = get_object_or_404(Lawyer, user=user)
            return ChatRoom.objects.filter(lawyer=lawyer, is_active=True)
        else:
            return ChatRoom.objects.none()


class MessageListView(generics.ListAPIView):
    """List messages in a chat room"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        chat_room_id = self.kwargs.get('chat_room_id')
        chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
        
        # Check if user has access to this chat room
        user = self.request.user
        if user.role == 'customer':
            client = get_object_or_404(Client, user=user)
            if chat_room.client != client:
                return Message.objects.none()
        elif user.role == 'lawyer':
            lawyer = get_object_or_404(Lawyer, user=user)
            if chat_room.lawyer != lawyer:
                return Message.objects.none()
        else:
            return Message.objects.none()
        
        # Mark messages as read for the current user
        unread_messages = chat_room.messages.filter(
            is_deleted=False,
            is_read=False
        ).exclude(sender=user)
        
        for message in unread_messages:
            message.mark_as_read()
        
        return chat_room.messages.filter(is_deleted=False)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        """Add chat_room to serializer context"""
        context = super().get_serializer_context()
        chat_room_id = self.kwargs.get('chat_room_id')
        context['chat_room'] = get_object_or_404(ChatRoom, id=chat_room_id)
        return context

    def perform_create(self, serializer):
        chat_room = serializer.context['chat_room']
        user = self.request.user

        # Check if user has access to this chat room
        if user.role == 'customer':
            client = get_object_or_404(Client, user=user)
            if chat_room.client != client:
                raise PermissionDenied("You don't have access to this chat room")
        elif user.role == 'lawyer':
            lawyer = get_object_or_404(Lawyer, user=user)
            if chat_room.lawyer != lawyer:
                raise PermissionDenied("You don't have access to this chat room")
        
        message = serializer.save()
        
        # Send real-time notification via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_room.id}",
            {
                'type': 'chat_message',
                'message': MessageSerializer(message, context={'request': self.request}).data
            }
        )
        
        # Create notification for the recipient
        recipient = chat_room.lawyer.user if user.role == 'customer' else chat_room.client.user
        ChatNotification.objects.create(
            recipient=recipient,
            sender=user,
            chat_room=chat_room,
            notification_type='new_message',
            title=f'New message in case {chat_room.case.case_number}',
            message=f'{user.phone_number} sent you a message'
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_chat_room(request, case_id):
    """Create a chat room for a case (only for admins or when case is assigned)"""
    case = get_object_or_404(Case, id=case_id)
    
    # Check if chat room already exists
    if hasattr(case, 'chat_room'):
        return Response(
            {'error': 'Chat room already exists for this case'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if case has both client and lawyer assigned
    if not case.lawyer:
        return Response(
            {'error': 'Case must have a lawyer assigned before creating chat room'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create chat room
    chat_room = ChatRoom.objects.create(
        case=case,
        client=case.client,
        lawyer=case.lawyer
    )
    
    # Create notifications for both parties
    ChatNotification.objects.create(
        recipient=case.client.user,
        chat_room=chat_room,
        notification_type='case_assigned',
        title=f'Chat room created for case {case.case_number}',
        message=f'You can now chat with your assigned lawyer'
    )
    
    ChatNotification.objects.create(
        recipient=case.lawyer.user,
        chat_room=chat_room,
        notification_type='case_assigned',
        title=f'Chat room created for case {case.case_number}',
        message=f'You can now chat with your client'
    )
    
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationListView(generics.ListAPIView):
    """List notifications for the authenticated user"""
    serializer_class = ChatNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ChatNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(
        ChatNotification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    
    return Response({'status': 'success'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the authenticated user"""
    ChatNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'status': 'success'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_stats(request):
    """Get chat statistics for the authenticated user"""
    user = request.user
    
    if user.role == 'customer':
        client = get_object_or_404(Client, user=user)
        chat_rooms = ChatRoom.objects.filter(client=client, is_active=True)
    elif user.role == 'lawyer':
        lawyer = get_object_or_404(Lawyer, user=user)
        chat_rooms = ChatRoom.objects.filter(lawyer=lawyer, is_active=True)
    else:
        chat_rooms = ChatRoom.objects.none()
    
    total_chats = chat_rooms.count()
    unread_messages = Message.objects.filter(
        chat_room__in=chat_rooms,
        is_deleted=False,
        is_read=False
    ).exclude(sender=user).count()
    
    unread_notifications = ChatNotification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    return Response({
        'total_chat_rooms': total_chats,
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications
    })
    
    
    
    
# chatApp/views.py
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_chat_room_by_case(request, case_id):
    """Get chat room by case ID"""
    chat_room = get_object_or_404(ChatRoom, case_id=case_id)
    
    # Check if user has access to this chat room
    user = request.user
    if user.role == 'customer':
        client = get_object_or_404(Client, user=user)
        if chat_room.client != client:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    elif user.role == 'lawyer':
        lawyer = get_object_or_404(Lawyer, user=user)
        if chat_room.lawyer != lawyer:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data)



# chatApp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import ChatRoom, Message

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_chat_room_read(request, chat_room_id):
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    # Mark all messages as read logic here
    return Response({'status': 'success'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_message_read(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.mark_as_read()
    return Response({'status': 'success'})