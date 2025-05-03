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
    try:
        with transaction.atomic():
            # Get the current logged-in user
            user = request.user
            submitted_user_id = request.data.get('user_id')
            
            if user:
                print(f"User ID: {user.id},\n User role: {user.role}\n")
                
            if submitted_user_id:
                print(f"Submitted User ID: {submitted_user_id}\n User role: {submitted_user_id.role}\n")
            else:
                print("No submitted user ID provided.\n")
            
           
            
            # Check if user has customer role
            if user.role != 'customer' and user.role !='admin':
                return Response(
                    {"error": "Only users with 'admin or customer' role can create a client profile"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if the user already has a client profile
            if user:
                existing_client = Client.objects.filter(user=user).first()
                if existing_client:
                    return Response(
                        {"error": "You already have a client profile"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif submitted_user_id:
                # Check if the submitted user ID exists and is a customer
                try:
                    user = CustomUser.objects.get(id=submitted_user_id, role='customer')
                    print(f"User ID: {user.id.role}, \n Submitted User ID: {submitted_user_id.role}")
                    existing_client = Client.objects.filter(user=user).first()
                    if existing_client:
                        return Response(
                            {"error": "This user already has a client profile"},
                            status=status.HTTP_400_BAD_REQUEST)
                except CustomUser.DoesNotExist:
                    return Response(
                        {"error": "User with this ID does not exist or is not a customer"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            # Validate national ID uniqueness
            national_id = request.data.get('national_id')
            if not national_id:
                return Response(
                    {"error": "National ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if Client.objects.filter(national_id=national_id).exists():
                return Response(
                    {"error": "This national ID is already registered"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create client data dict
            client_data = request.data.copy()
            
            # Create serializer instance with data and validate
            serializer = ClientSerializer(data=client_data)
            if serializer.is_valid():
                # Save the client with the current user
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
    if not request.user:
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
    if not request.user:
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
    if not request.user:
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
    if not request.user:
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