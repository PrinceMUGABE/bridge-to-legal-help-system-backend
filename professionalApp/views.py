from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.http import Http404

from .models import Lawyer
from .serializers import LawyerSerializer
from userApp.models import CustomUser


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_lawyer(request):
    """
    Create a new lawyer profile with all validations in the view
    """
    try:
        # Validate required fields
        if not request.data.get('first_name'):
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'first_name': 'First name is required'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.data.get('last_name'):
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'last_name': 'Last name is required'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate user_id
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'user_id': 'User is required'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check that the user exists and is a lawyer
        try:
            user = CustomUser.objects.get(id=user_id)
            if user.role != 'lawyer':
                return Response({
                    'status': 'error',
                    'message': 'Validation error',
                    'errors': {'user_id': "User must have the 'lawyer' role"}
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Check if this user already has a lawyer profile
            if Lawyer.objects.filter(user_id=user_id).exists():
                return Response({
                    'status': 'error',
                    'message': 'Validation error',
                    'errors': {'user_id': "This user already has a lawyer profile"}
                }, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Validation error',
                'errors': {'user_id': "User with this ID does not exist"}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # Use transaction to ensure database consistency
        with transaction.atomic():
            # Extract data for Lawyer model (excluding user_id)
            lawyer_data = {k: v for k, v in request.data.items() if k != 'user_id'}
            
            # Create lawyer instance
            lawyer = Lawyer(
                user=user,
                created_by=request.user,
                **lawyer_data
            )
            lawyer.save()
            
            # Return the created lawyer data
            serializer = LawyerSerializer(lawyer)
            return Response({
                'status': 'success',
                'message': 'Lawyer profile created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except IntegrityError as e:
        return Response({
            'status': 'error',
            'message': 'Database integrity error',
            'errors': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_lawyers(request):
    """
    Get all lawyers with filtering options
    """
    try:
        # Get query parameters for filtering
        status_filter = request.query_params.get('status')
        district = request.query_params.get('district')
        sector = request.query_params.get('sector')
        availability = request.query_params.get('availability')
        
        # Start with all lawyers
        lawyers = Lawyer.objects.all()
        
        # Apply filters if provided
        if status_filter:
            lawyers = lawyers.filter(status=status_filter)
            
        if district:
            lawyers = lawyers.filter(residence_district__icontains=district)
            
        if sector:
            lawyers = lawyers.filter(residence_sector__icontains=sector)
            
        if availability:
            lawyers = lawyers.filter(availability_status=availability)
        
        # For list view, select only necessary fields
        lawyers_list = lawyers.values(
            'id', 'first_name', 'middle_name', 'last_name',
            'residence_district', 'residence_sector', 'years_of_experience',
            'status', 'availability_status'
        ).select_related('user')
        
        # Format the response data with computed fields
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
            # Update fields directly
            for field, value in request.data.items():
                if hasattr(lawyer, field) and field not in ('user', 'created_at', 'updated_at', 'created_by'):
                    setattr(lawyer, field, value)
            
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
        
        # Get query parameters for filtering
        status_filter = request.query_params.get('status')
        
        # Apply filters if provided
        if status_filter:
            lawyers = lawyers.filter(status=status_filter)
        
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
        district = request.query_params.get('district')
        sector = request.query_params.get('sector')
        
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