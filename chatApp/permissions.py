# chatApp/permissions.py
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import ChatRoom
from clientApp.models import Client
from professionalApp.models import Lawyer


class IsChatRoomParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a chat room to access it.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        chat_room_id = view.kwargs.get('chat_room_id') or view.kwargs.get('pk')
        if not chat_room_id:
            return False
        
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id)
            return self.is_participant(request.user, chat_room)
        except ChatRoom.DoesNotExist:
            return False
    
    def is_participant(self, user, chat_room):
        """Check if user is a participant in the chat room"""
        if user.role == 'customer':
            try:
                client = Client.objects.get(user=user)
                return chat_room.client == client
            except Client.DoesNotExist:
                return False
        elif user.role == 'lawyer':
            try:
                lawyer = Lawyer.objects.get(user=user)
                return chat_room.lawyer == lawyer
            except Lawyer.DoesNotExist:
                return False
        return False


class IsClientOrLawyer(permissions.BasePermission):
    """
    Custom permission to only allow clients or lawyers to access chat features.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['customer', 'lawyer']
        )


class CanCreateChatRoom(permissions.BasePermission):
    """
    Custom permission to check if user can create chat rooms.
    Only admins or when specific conditions are met.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can always create chat rooms
        if request.user.role == 'admin':
            return True
        
        # For now, restrict chat room creation to admins only
        # This can be modified based on business requirements
        return False