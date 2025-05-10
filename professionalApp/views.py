from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.http import Http404

from .models import Lawyer
from .serializers import LawyerSerializer
from userApp.models import CustomUser
import random
import string
import re
from django.core.mail import send_mail
from userApp.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.timezone import now
from speciliarizationApp.models import Specialization

def is_valid_password(password):
    """Validate password complexity."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not any(char.isdigit() for char in password):
        return "Password must include at least one number."
    if not any(char.isupper() for char in password):
        return "Password must include at least one uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must include at least one lowercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must include at least one special character (!@#$%^&* etc.)."
    return None




def is_valid_email(email):
    """Validate email format and domain."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    # Check format
    if not re.match(email_regex, email):
        return "Invalid email format."



    #check if entered password has been used before
    if not email.endswith("@gmail.com"):
        return "Only Gmail addresses are allowed for registration."

    return None



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
def create_lawyer(request):
    """
    Create a new lawyer profile with all validations in the view
    """
    
    print(f"Submitted Data: {request.data}\n")
    
    try:
        # Validate input data presence
        if not request.data:
            print("Error: No data submitted")
            return Response(
                {"error": "No data submitted. Please provide information."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate required fields
        try:
            phone_number = request.data.get('phone_number', '').strip()
            email = request.data.get('email', '').strip()
            national_id = request.data.get('national_id', '').strip()
            national_id_image = request.FILES.get('national_id_card')
            diploma = request.FILES.get('diploma')
            first_name = request.data.get('first_name', '').strip()
            last_name = request.data.get('last_name', '').strip()
            middle_name = request.data.get('middle_name', '').strip()
            gender = request.data.get('gender', 'other').strip()
            availability_status = request.data.get('availability_status', 'inactive').strip()
            marital_status = request.data.get('marital_status', 'single').strip()
            education_level = request.data.get('education_level', 'bachelor').strip()
            years_of_experience = request.data.get('years_of_experience', 0)
            residence_district = request.data.get('residence_district', '').strip()
            residence_sector = request.data.get('residence_sector', '').strip()
            bio = request.data.get('bio', '').strip()
            
            # FIX: Retrieve specializations as a list (getlist instead of get)
            # And use the correct field name (specializations - plural)
            specializations = request.data.getlist('specializations')
            
            # Print extracted values for debugging
            print(f"Extracted Values:")
            print(f"  Phone: {phone_number}")
            print(f"  Email: {email}")
            print(f"  National ID: {national_id}")
            print(f"  First Name: {first_name}")
            print(f"  Last Name: {last_name}")
            print(f"  Files: {request.FILES.keys()}")
            print(f"  Specializations: {specializations}")  # Updated to print all specializations
            
        except Exception as e:
            error_msg = f"Error extracting fields: {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            return Response(
                {"error": error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Comprehensive validation
        validation_errors = []

        # Phone number validation
        if not phone_number:
            validation_errors.append("Phone number is required")
        elif not phone_number.startswith('0') or len(''.join(filter(str.isdigit, phone_number))) != 10:
            validation_errors.append("Phone number must be 10 digits long and start with 0")

        # Email validation
        if not email:
            validation_errors.append("Email is required")
        else:
            try:
                validate_email(email)
                
                # Additional email validation
                email_error = is_valid_email(email)
                if email_error:
                    validation_errors.append(email_error)
            except ValidationError:
                validation_errors.append("Invalid email format")

        # Specialization validation
        if not specializations:
            validation_errors.append("At least one specialization is required")

        # Check for existing user with same phone number or email
        existing_user_phone = CustomUser.objects.filter(phone_number=phone_number).exists()
        if existing_user_phone:
            validation_errors.append("Phone number already registered")

        existing_user_email = CustomUser.objects.filter(email=email).exists()
        if existing_user_email:
            validation_errors.append("Email already registered")

        # National ID validation
        if not national_id:
            validation_errors.append("National ID number is required")
        elif not national_id.isdigit() or len(national_id) != 16:
            validation_errors.append("National ID must be 16 digits long")
        
        # Check if national ID is already used
        if Lawyer.objects.filter(national_id_number=national_id).exists():
            validation_errors.append("National ID already registered")

        # National ID image file validation
        if not national_id_image:
            validation_errors.append("National ID card file is required")
        else:
            if not isinstance(national_id_image, InMemoryUploadedFile):
                validation_errors.append("Invalid national ID card file")
            elif national_id_image.size > 5 * 1024 * 1024:
                validation_errors.append("National ID card file too large. Max 5MB allowed.")
            elif national_id_image.content_type != 'application/pdf':
                validation_errors.append("National ID card must be a PDF file")

        # Diploma file validation
        if not diploma:
            validation_errors.append("Diploma file is required")
        else:
            if not isinstance(diploma, InMemoryUploadedFile):
                validation_errors.append("Invalid diploma file")
            elif diploma.size > 5 * 1024 * 1024:
                validation_errors.append("Diploma file too large. Max 5MB allowed.")
            elif diploma.content_type != 'application/pdf':
                validation_errors.append("Diploma must be a PDF file")

        # Return validation errors if any
        if validation_errors:
            print("Validation Errors:", validation_errors)
            return Response(
                {"errors": validation_errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use transaction to ensure database consistency
        with transaction.atomic():
            # Generate a temporary password
            temp_password = generate_secure_password()
            
            # Create user with lawyer role
            user = CustomUser.objects.create_user(
                phone_number=phone_number,
                email=email,
                role='lawyer', 
                password=temp_password
            )
            
            # Create lawyer profile
            lawyer = Lawyer.objects.create(
                user=user,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                gender=gender,
                marital_status=marital_status,
                residence_district=residence_district,
                residence_sector=residence_sector,
                availability_status=availability_status,
                education_level=education_level,
                years_of_experience=years_of_experience,
                national_id_number=national_id,  # Fixed field name to match model
                national_id_card=national_id_image,
                diploma=diploma,
                bio=bio,
                created_by=request.user,
                status='pending',
                created_at=now(),
                updated_at=now()
            )
            
            # Add specializations to the lawyer
            if specializations:
                for spec_id in specializations:
                    try:
                        specialization = Specialization.objects.get(pk=int(spec_id))
                        lawyer.specializations.add(specialization)
                    except (Specialization.DoesNotExist, ValueError) as e:
                        print(f"Warning: Could not add specialization {spec_id}: {e}")
            
            # Send the password to the user's email if email is provided
            if email:
                message = (
                    f"Hello, {first_name} {last_name}\n\n"
                    f"You have been added to the Bridge to Legal Help System (BLHS).\n"
                    f"Your password is: {temp_password}\n\n"
                    "This is a system-generated password. Please change it after your first login."
                )
                
                send_mail(
                    subject="Welcome to Bridge to Legal Help System",
                    message=message,
                    from_email="no-reply@blhs.com",
                    recipient_list=[email],
                )
                
            # Prepare response data
            response_data = {
                'id': lawyer.id,
                'first_name': lawyer.first_name,
                'last_name': lawyer.last_name,
                'status': lawyer.status,
                'availability_status': lawyer.availability_status,
                'residence_district': lawyer.residence_district,
                'residence_sector': lawyer.residence_sector,
                'years_of_experience': lawyer.years_of_experience,
                'created_at': lawyer.created_at,
                'updated_at': lawyer.updated_at,
                'created_by': lawyer.created_by.phone_number if lawyer.created_by else None,
                'national_id': lawyer.national_id_number,
                'specializations': list(lawyer.specializations.values('id', 'name')) # Include specializations in response
            }
            
            print("Lawyer created successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
    except IntegrityError as e:
        error_msg = f"Database integrity error: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'message': 'Database integrity error',
            'errors': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_lawyer(request, lawyer_id):
    """
    Update lawyer details with validations in the view
    """
    try:
        lawyer = get_object_or_404(Lawyer, id=lawyer_id)
        
        # Check if the user has permission to update this lawyer
        if not (request.user.is_staff or request.user == lawyer.user or request.user == lawyer.created_by):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to update this lawyer profile'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Field validations for update
        if 'first_name' in request.data and not request.data.get('first_name'):
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'first_name': 'First name cannot be empty'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'last_name' in request.data and not request.data.get('last_name'):
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'last_name': 'Last name cannot be empty'}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Use transaction to ensure database consistency
        with transaction.atomic():
            # Handle regular fields update
            for field, value in request.data.items():
                if hasattr(lawyer, field) and field not in ('user', 'created_at', 'updated_at', 'created_by', 
                                                         'specializations', 'diploma', 'national_id_card'):
                    setattr(lawyer, field, value)
            
            # Handle specializations update
            if 'specializations' in request.data:
                specializations = request.data.getlist('specializations')
                if specializations:
                    # Create a list of specialization objects
                    spec_objects = []
                    for spec_id in specializations:
                        try:
                            specialization = Specialization.objects.get(pk=int(spec_id))
                            spec_objects.append(specialization)
                        except (Specialization.DoesNotExist, ValueError) as e:
                            print(f"Warning: Could not add specialization {spec_id}: {e}")
                    
                    # Set the specializations
                    lawyer.specializations.set(spec_objects)
            
            # Handle diploma file upload
            if 'diploma' in request.FILES:
                # Delete old file if it exists
                if lawyer.diploma:
                    try:
                        # Get the file path
                        old_file_path = lawyer.diploma.path
                        # Delete the file from the filesystem
                        import os
                        if os.path.isfile(old_file_path):
                            os.remove(old_file_path)
                    except Exception as e:
                        # Just log the error but continue
                        print(f"Error deleting old diploma file: {e}")
                
                # Set new diploma
                lawyer.diploma = request.FILES['diploma']
            
            # Handle national ID card file upload
            if 'national_id_card' in request.FILES:
                # Delete old file if it exists
                if lawyer.national_id_card:
                    try:
                        # Get the file path
                        old_file_path = lawyer.national_id_card.path
                        # Delete the file from the filesystem
                        import os
                        if os.path.isfile(old_file_path):
                            os.remove(old_file_path)
                    except Exception as e:
                        # Just log the error but continue
                        print(f"Error deleting old national ID card file: {e}")
                
                # Set new national ID card
                lawyer.national_id_card = request.FILES['national_id_card']
            
            # Update the timestamp and save
            lawyer.updated_at = now()
            lawyer.save()
            
            # Return the updated lawyer data
            serializer = LawyerSerializer(lawyer)
            return Response({
                'status': 'success',
                'message': 'Lawyer profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
    except Http404:
        return Response({
            'status': 'error',
            'message': f'Lawyer with ID {lawyer_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
               
        
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_lawyers(request):
    """
    Get all lawyers using serializer for consistent data formatting
    """
    try:
        # Get all lawyers with their related data
        lawyers = Lawyer.objects.all()

        # Use the serializer to format the data
        serializer = LawyerSerializer(lawyers, many=True)
        
        print(f"Lawyers retrieved: {serializer.data}\n\n")

        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
             
            
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lawyer_by_id(request, lawyer_id):
    """
    Get lawyer details by ID
    """
    try:
        lawyer = get_object_or_404(Lawyer, id=lawyer_id)
        serializer = LawyerSerializer(lawyer)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Http404:
        return Response({
            'status': 'error',
            'message': f'Lawyer with ID {lawyer_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





             



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_lawyer(request, lawyer_id):
    """
    Delete a lawyer profile
    """
    try:
        lawyer = get_object_or_404(Lawyer, id=lawyer_id)
        
        # Check if the user has permission to delete this lawyer
        if not (request.user.is_staff or request.user == lawyer.created_by):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to delete this lawyer profile'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # Get the lawyer name before deletion for confirmation message
        lawyer_name = f"{lawyer.first_name} {lawyer.last_name}"
        
        # Delete the lawyer
        lawyer.delete()
        
        return Response({
            'status': 'success',
            'message': f'Lawyer profile for {lawyer_name} deleted successfully'
        }, status=status.HTTP_200_OK)
            
    except Http404:
        return Response({
            'status': 'error',
            'message': f'Lawyer with ID {lawyer_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lawyers_created_by_user(request):
    """
    Get all lawyers created by the logged-in user
    """
    try:
        lawyers = Lawyer.objects.filter(created_by=request.user)
        
        # Format for list response
        response_data = []
        for lawyer in lawyers:
            middle = f" {lawyer.middle_name}" if lawyer.middle_name else ""
            full_name = f"{lawyer.first_name}{middle} {lawyer.last_name}"
            
            response_data.append({
                'id': lawyer.id,
                'full_name': full_name,
                'user_phone': lawyer.user.phone_number if lawyer.user else None,
                'residence_district': lawyer.residence_district,
                'residence_sector': lawyer.residence_sector,
                'years_of_experience': lawyer.years_of_experience,
                'status': lawyer.status,
                'availability_status': lawyer.availability_status
            })
        
        return Response({
            'status': 'success',
            'count': len(response_data),
            'data': response_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logged_in_lawyer_info(request):
    """
    Get lawyer information for the logged-in user if they have a lawyer profile
    """
    try:
        try:
            lawyer = Lawyer.objects.get(user=request.user)
        except Lawyer.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No lawyer profile found for the logged-in user'
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = LawyerSerializer(lawyer)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lawyers_by_residence(request):
    """
    Get lawyers filtered by residence (district and/or sector)
    """
    try:
        # Get query parameters
        district = request.data.get('district')
        sector = request.data.get('sector')
        
        # Validate at least one filter is provided - validation in view
        if not district and not sector:
            return Response({
                'status': 'error',
                'message': 'At least one filter (district or sector) must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Build the filter based on provided parameters
        filters = Q()
        
        if district:
            filters &= Q(residence_district__icontains=district)
            
        if sector:
            filters &= Q(residence_sector__icontains=sector)
            
        lawyers = Lawyer.objects.filter(filters)
        
        # Only include accepted and active lawyers by default
        status_filter = request.query_params.get('status', 'accepted')
        availability = request.query_params.get('availability', 'active')
        
        if status_filter:
            lawyers = lawyers.filter(status=status_filter)
            
        if availability:
            lawyers = lawyers.filter(availability_status=availability)
        
        # Format response similar to list view
        response_data = []
        for lawyer in lawyers:
            middle = f" {lawyer.middle_name}" if lawyer.middle_name else ""
            full_name = f"{lawyer.first_name}{middle} {lawyer.last_name}"
            
            response_data.append({
                'id': lawyer.id,
                'full_name': full_name,
                'user_phone': lawyer.user.phone_number if lawyer.user else None,
                'residence_district': lawyer.residence_district,
                'residence_sector': lawyer.residence_sector,
                'years_of_experience': lawyer.years_of_experience,
                'status': lawyer.status,
                'availability_status': lawyer.availability_status
            })
        
        return Response({
            'status': 'success',
            'count': len(response_data),
            'data': response_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'errors': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)