# templates/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Template
from .serializers import (
    TemplateSerializer,
    TemplateCreateUpdateSerializer,
    TemplateListSerializer
)
from django.db import models


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Template
from .serializers import TemplateListSerializer, TemplateSerializer, TemplateCreateUpdateSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_templates(request):
    """
    Get all active templates with optional filtering and searching
    """
    try:
        # Start with all templates first, then apply filters
        templates = Template.objects.all()
        
        # Debug: Print total template count
        print(f"\n\nTotal templates in database: {templates.count()}")

        serializer = TemplateListSerializer(templates, many=True, context={'request': request})
        
        # print(f"Serialized data: {serializer.data}")
        
        return Response({
            'success': True,
            'count': templates.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error in get_all_templates: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error retrieving templates: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Alternative version for testing - removes the is_active filter
@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_templates_debug(request):
    """
    Debug version - gets ALL templates regardless of is_active status
    """
    try:
        templates = Template.objects.all().order_by('-downloads', '-rating', '-created_at')
        
        print(f"\n\nDEBUG: Total templates found: {templates.count()}")
        for template in templates:
            print(f"Template: ID={template.id}, Title='{template.title}', Active={template.is_active}")
        
        serializer = TemplateListSerializer(templates, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'count': templates.count(),
            'data': serializer.data,
            'debug_info': {
                'total_templates': Template.objects.count(),
                'active_templates': Template.objects.filter(is_active=True).count(),
                'inactive_templates': Template.objects.filter(is_active=False).count(),
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error in debug view: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error retrieving templates: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        

@api_view(['GET'])
@permission_classes([AllowAny])
def get_template_detail(request, template_id):
    """
    Get detailed information about a specific template
    """
    try:
        template = get_object_or_404(Template, id=template_id, is_active=True)
        serializer = TemplateSerializer(template, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Template.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving template: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_template(request):
    """
    Create a new template
    """
    try:
        print(f"\n\n submitted data: {request.data}\n\n")
        serializer = TemplateCreateUpdateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            template = serializer.save()
            response_serializer = TemplateSerializer(template, context={'request': request})
            print("Template added successfully")
            
            return Response({
                'success': True,
                'message': 'Template created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            print(f"\n Validation error: {serializer.errors}\n")
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
   
    except Exception as e:
        print(f'\nError creating template: {str(e)}\n')
        return Response({
            'success': False,
            'message': f'Error creating template: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def update_template(request, template_id):
    """
    Update an existing template
    """
    try:
        template = get_object_or_404(Template, id=template_id)
        
        # Use partial=True for PATCH requests
        partial = request.method == 'PATCH'
        serializer = TemplateCreateUpdateSerializer(
            template, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_template = serializer.save()
            response_serializer = TemplateSerializer(updated_template, context={'request': request})
            
            return Response({
                'success': True,
                'message': 'Template updated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Template.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error updating template: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_template(request, template_id):
    """
    Delete a template (soft delete by setting is_active=False)
    """
    try:
        template = get_object_or_404(Template, id=template_id)
        
        # Soft delete
        template.is_active = False
        template.save()
        
        return Response({
            'success': True,
            'message': 'Template deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Template.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error deleting template: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def download_template(request, template_id):
    """
    Handle template download and increment download count
    """
    try:
        template = get_object_or_404(Template, id=template_id)
        
        # Increment download count
        template.increment_downloads()
        
        # Return template details with file URL
        serializer = TemplateSerializer(template, context={'request': request})
        
        return Response({
            'success': True,
            'message': 'Template download initiated',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Template.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error processing download: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_template_categories(request):
    """
    Get all available template categories
    """
    try:
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Template.CATEGORY_CHOICES
        ]
        
        return Response({
            'success': True,
            'data': categories
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving categories: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_template_statistics(request):
    """
    Get template library statistics
    """
    try:
        active_templates = Template.objects.filter(is_active=True)
        
        total_templates = active_templates.count()
        total_downloads = sum(template.downloads for template in active_templates)
        total_categories = len(Template.CATEGORY_CHOICES)
        average_rating = active_templates.aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0
        
        statistics = {
            'total_templates': total_templates,
            'total_downloads': total_downloads,
            'total_categories': total_categories,
            'average_rating': round(float(average_rating), 1)
        }
        
        return Response({
            'success': True,
            'data': statistics
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_popular_templates(request):
    """
    Get popular templates (top 10 by downloads)
    """
    try:
        limit = int(request.GET.get('limit', 10))
        popular_templates = Template.objects.filter(is_active=True).order_by('-downloads')[:limit]
        
        serializer = TemplateListSerializer(popular_templates, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error retrieving popular templates: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)