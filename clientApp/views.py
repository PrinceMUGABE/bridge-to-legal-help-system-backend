from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.timezone import now

from .models import Client
from .serializers import ClientSerializer
from userApp.models import CustomUser


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_client(request):
    """
    Create a new client profile
    """
    # Check if the user has permission to create clients
    if not request.user.has_perm('client.add_client'):
        return Response(
            {"error": "You don't have permission to create clients"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        with transaction.atomic():
            # Extract user_id from request data
            user_id = request.user
            if not user_id:
                return Response(
                    {"error": "User ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user exists and has customer role
            try:
                user = CustomUser.objects.get(id=user_id)
                if user.role != 'customer':
                    return Response(
                        {"error": "Only 'customer' user is allowed to create a client profile"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": f"User with ID {user_id} does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if the user already has a client profile
            if Client.objects.filter(user=user).exists():
                return Response(
                    {"error": "This user already has a client profile"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validate national ID uniqueness
            national_id = request.data.get('national_id')
            if Client.objects.filter(national_id=national_id).exists():
                return Response(
                    {"error": "This national ID is already registered"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create client data dict and add user and created_by fields
            client_data = request.data.copy()
            client_data['user'] = user.id
            
            serializer = ClientSerializer(data=client_data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": f"Failed to create client: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_clients(request):
    """
    Get all clients with filtering options
    """
    # Check if the user has permission to view clients
    if not request.user.has_perm('client.view_client'):
        return Response(
            {"error": "You don't have permission to view clients"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get query parameters for filtering
        status_filter = request.query_params.get('status')
        province = request.query_params.get('province')
        district = request.query_params.get('district')
        
        # Start with all clients
        clients = Client.objects.all()
        
        # Apply filters if provided
        if status_filter:
            clients = clients.filter(status=status_filter)
        if province:
            clients = clients.filter(province__icontains=province)
        if district:
            clients = clients.filter(district__icontains=district)
        
        serializer = ClientSerializer(clients, many=True)
        
        if not clients:
            return Response(
                {"message": "No clients found"},
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve clients: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_client_by_id(request, client_id):
    """
    Get a specific client by ID
    """
    # Check if the user has permission to view clients
    if not request.user.has_perm('client.view_client'):
        return Response(
            {"error": "You don't have permission to view client details"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        client = get_object_or_404(Client, id=client_id)
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve client: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clients_created_by_user(request):
    """
    Get all clients created by the logged-in user
    """
    try:
        clients = Client.objects.filter(created_by=request.user)
        
        if not clients:
            return Response(
                {"message": "You don't have client profile"},
                status=status.HTTP_200_OK
            )
            
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve clients: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_client(request, client_id):
    """
    Update a client's information
    """
    # Check if the user has permission to update clients
    if not request.user.has_perm('client.change_client'):
        return Response(
            {"error": "You don't have permission to update client information"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        client = get_object_or_404(Client, id=client_id)
        
        # Validate national ID uniqueness if it's being changed
        national_id = request.data.get('national_id')
        if national_id and national_id != client.national_id:
            if Client.objects.filter(national_id=national_id).exists():
                return Response(
                    {"error": "This national ID is already registered"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Use partial=True to allow partial updates
        is_partial = request.method == 'PATCH'
        serializer = ClientSerializer(client, data=request.data, partial=is_partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": f"Failed to update client: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_client(request, client_id):
    """
    Delete a client
    """
    # Check if the user has permission to delete clients
    if not request.user.has_perm('client.delete_client'):
        return Response(
            {"error": "You don't have permission to delete clients"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        client = get_object_or_404(Client, id=client_id)
        
        # Option 1: Hard delete
        client.delete()
        
        # Option 2: Soft delete (if preferred)
        # client.status = 'inactive'
        # client.save()
        
        return Response(
            {"message": "Client deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
        
    except Exception as e:
        return Response(
            {"error": f"Failed to delete client: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )