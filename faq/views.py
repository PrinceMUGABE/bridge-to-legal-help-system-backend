# faq/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import FAQ
from .serializers import FAQSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_faqs(request):
    """Get all active FAQs with optional filtering"""
    faqs = FAQ.objects.filter(is_active=True)
    
    # Filter by category
    category = request.GET.get('category')
    if category and category != 'all':
        faqs = faqs.filter(category=category)
    
    # Filter by search term
    search = request.GET.get('search')
    if search:
        faqs = faqs.filter(
            Q(question__icontains=search) | 
            Q(answer__icontains=search)
        )
    
    # Sort FAQs (popular first, then by creation date)
    faqs = faqs.order_by('-popular', '-created_at')
    
    serializer = FAQSerializer(faqs, many=True)
    return Response({
        'count': faqs.count(),
        'faqs': serializer.data
    })


@api_view(['GET'])
def get_faq(request, faq_id):
    """Get single FAQ by ID"""
    faq = get_object_or_404(FAQ, id=faq_id, is_active=True)
    serializer = FAQSerializer(faq)
    return Response(serializer.data)


@api_view(['GET'])
def get_popular_faqs(request):
    """Get popular FAQs"""
    faqs = FAQ.objects.filter(is_active=True, popular=True).order_by('-created_at')
    serializer = FAQSerializer(faqs, many=True)
    return Response({
        'count': faqs.count(),
        'faqs': serializer.data
    })


@api_view(['GET'])
def get_categories(request):
    """Get all categories with FAQ counts"""
    categories = []
    
    # Add 'all' category
    total_count = FAQ.objects.filter(is_active=True).count()
    categories.append({
        'id': 'all',
        'name': 'All Categories',
        'count': total_count
    })
    
    # Add individual categories
    for category_id, category_name in FAQ.CATEGORY_CHOICES:
        count = FAQ.objects.filter(category=category_id, is_active=True).count()
        categories.append({
            'id': category_id,
            'name': category_name,
            'count': count
        })
    
    return Response(categories)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_faq(request):
    """Create new FAQ (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can create FAQs'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = FAQSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_faq(request, faq_id):
    """Update FAQ (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can update FAQs'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    faq = get_object_or_404(FAQ, id=faq_id)
    serializer = FAQSerializer(faq, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_faq(request, faq_id):
    """Delete FAQ (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can delete FAQs'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    faq = get_object_or_404(FAQ, id=faq_id)
    faq.delete()
    return Response(
        {'message': 'FAQ deleted successfully'}, 
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(['GET'])
def search_faqs(request):
    """Search FAQs by query"""
    query = request.GET.get('q', '')
    if not query:
        return Response(
            {'error': 'Search query is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    faqs = FAQ.objects.filter(
        is_active=True
    ).filter(
        Q(question__icontains=query) | 
        Q(answer__icontains=query)
    ).order_by('-popular', '-created_at')
    
    serializer = FAQSerializer(faqs, many=True)
    return Response({
        'query': query,
        'count': faqs.count(),
        'results': serializer.data
    })