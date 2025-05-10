# Views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import SpecializationSerializer
from rest_framework import status, permissions
from .models import Specialization

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_specialization(request):
    """Create a new specialization"""
    try:
        serializer = SpecializationSerializer(data=request.data)
        if serializer.is_valid():
            # Set the current user as creator
            serializer.save(created_by=request.user)
            return Response({
                'status': 'success',
                'message': 'Specialization created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_specializations(request):
    """Get all specializations"""
    try:
        # Allow filtering by active status if provided
        active_filter = request.query_params.get('active')
        specializations = Specialization.objects.all()
        
        if active_filter is not None:
            active_value = active_filter.lower() == 'true'
            specializations = specializations.filter(active=active_value)
            
        serializer = SpecializationSerializer(specializations, many=True)
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

@api_view(['GET'])
@permission_classes([AllowAny])
def get_specialization_by_id(request, id):
    """Get a specialization by ID"""
    try:
        specialization = get_object_or_404(Specialization, id=id)
        serializer = SpecializationSerializer(specialization)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Specialization.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Specialization not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

@api_view(['GET'])
@permission_classes([AllowAny])
def get_specialization_by_status(request, status):
    """Get a specialization by name"""
    try:
        # Case-insensitive search
        specialization = get_object_or_404(Specialization, status__iexact=status)
        serializer = SpecializationSerializer(specialization)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Specialization.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Specialization not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_specialization(request, id):
    """Update a specialization"""
    print(f"Submitted data: {request.data}\n\n")
    try:
        
        specialization = get_object_or_404(Specialization, id=id)
        
        # Optional permission check - only creator or admin can update
        if specialization.created_by != request.user and request.user.role != 'admin':
            return Response({
                'status': 'error',
                'message': 'You do not have permission to update this specialization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Use partial=True for PATCH requests
        is_partial = request.method == 'PATCH'
        serializer = SpecializationSerializer(
            specialization, 
            data=request.data, 
            partial=is_partial
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Specialization updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Specialization.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Specialization not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_specialization(request, id):
    """Delete a specialization"""
    try:
        specialization = get_object_or_404(Specialization, id=id)
        
        # Optional permission check - only creator or admin can delete
        if specialization.created_by != request.user and request.user.role != 'admin':
            return Response({
                'status': 'error',
                'message': 'You do not have permission to delete this specialization'
            }, status=status.HTTP_403_FORBIDDEN)
        
        specialization.delete()
        return Response({
            'status': 'success',
            'message': 'Specialization deleted successfully'
        }, status=status.HTTP_200_OK)
    except Specialization.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Specialization not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_specializations(request):
    """Get all specializations created by the logged-in user"""
    try:
        specializations = Specialization.objects.filter(created_by=request.user)
        
        # Allow filtering by active status if provided
        active_filter = request.query_params.get('active')
        if active_filter is not None:
            active_value = active_filter.lower() == 'true'
            specializations = specializations.filter(active=active_value)
            
        serializer = SpecializationSerializer(specializations, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        
        
        
        
        
        
        
        
        