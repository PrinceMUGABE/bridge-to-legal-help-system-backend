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
from userApp.views import register_user
from userApp.serializers import UserSerializer
import random
import string
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.db.utils import IntegrityError
from .models import CustomUser
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
import random
import string

def generate_secure_password():
    """Generate a secure random password that meets complexity requirements."""
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*(),.?\":{}|<>"
    
    # Ensure at least one of each required character type
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars)
    ]
    
    # Fill remaining length with random characters from all types
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(4))  # 4 more chars to make it 8 total
    
    # Shuffle the password characters
    random.shuffle(password)
    return ''.join(password)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_client(request):
    """
    Create a new client profile.
    
    This function handles three scenarios:
    1. Customer users creating their own profile
    2. Admin users creating a new customer user and associated client profile
    3. Professional users creating a new customer user and associated client profile
    """
    try:
        with transaction.atomic():
            # Get the current logged-in user
            user = request.user
            
            # Check if user exists and has appropriate role
            if not user:
                return Response(
                    {"error": "You are not logged in"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            # Check if user has appropriate role
            if user.role not in ['customer', 'admin', 'professional']:
                return Response(
                    {"error": "Only users with 'admin', 'customer', or 'professional' role can create a client profile"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize variable to track if admin or professional is creating a new user
            is_creating_new_user = user.role in ['admin', 'professional']
            client_user = user  # Default: user creating their own profile
            
            # Admin or Professional creating a new user case
            if is_creating_new_user:
                phone_number = request.data.get('phone_number')
                email = request.data.get('email')
                
                if not phone_number or not email:
                    return Response(
                        {"error": "Phone number and email are required for new users"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
                # Check if user with this phone number already exists
                if CustomUser.objects.filter(phone_number=phone_number).exists():
                    return Response(
                        {"error": "This phone number is already registered"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check if user with this email already exists
                if CustomUser.objects.filter(email=email).exists():
                    return Response(
                        {"error": "This email is already registered"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Generate secure password for new user
                password = generate_secure_password()
                
                # Create new user with customer role
                client_user = CustomUser.objects.create_user(
                    phone_number=phone_number,
                    email=email,
                    role='customer',
                    password=password  # This will be hashed by create_user
                )
                client_user.created_by = user  # Track who created this user
                client_user.save()
                
                # Send email with generated password
                if email:
                    message = (
                        "Hello,\n\nYour account has been created in The Bridge to Legal Help System (BLHS).\n"
                        f"Your password is: {password}\n\n"
                        "This is a system-generated password. Please change it after your first login."
                    )
                    
                    # Add information about who created the account
                    if user.role == 'admin':
                        message += "\nYour account was created by an administrator."
                    elif user.role == 'professional':
                        message += "\nYour account was created by a legal professional."
                    
                    send_mail(
                        subject="Your Account Password",
                        message=message,
                        from_email="no-reply@gmail.com",
                        recipient_list=[email],
                    )
            else:
                # User creating their own profile - check if they already have one
                existing_client = Client.objects.filter(user=user).first()
                if existing_client:
                    return Response(
                        {"error": "You already have a client profile"},
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
                # Save the client with the appropriate user (either newly created or current user)
                serializer.save(user=client_user)
                
                response_data = serializer.data
                if is_creating_new_user:
                    # Include basic user information in response when admin/professional creates a new user
                    response_data['user_details'] = {
                        'phone_number': client_user.phone_number,
                        'email': client_user.email,
                        'id': client_user.id
                    }
                    
                return Response(response_data, status=status.HTTP_201_CREATED)
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