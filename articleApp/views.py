# articles/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Article
from .serializers import ArticleSerializer, ArticleListSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_articles(request):
    """Get all articles with optional filtering"""
    articles = Article.objects.all()
    
    # Filter by category
    category = request.GET.get('category')
    if category and category != 'all':
        articles = articles.filter(category=category)
    
    # Filter by search term
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | 
            Q(excerpt__icontains=search) | 
            Q(content__icontains=search)
        )
    
    # Sort articles
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'newest':
        articles = articles.order_by('-date')
    elif sort_by == 'oldest':
        articles = articles.order_by('date')
    elif sort_by == 'popular':
        articles = articles.order_by('-views')
    
    serializer = ArticleListSerializer(articles, many=True)
    return Response({
        'count': articles.count(),
        'articles': serializer.data
    })


@api_view(['GET'])
def get_article(request, article_id):
    """Get single article by ID and increment views"""
    article = get_object_or_404(Article, id=article_id)
    
    # Increment views
    article.views += 1
    article.save(update_fields=['views'])
    
    serializer = ArticleSerializer(article)
    return Response(serializer.data)


@api_view(['GET'])
def get_featured_articles(request):
    """Get featured articles"""
    articles = Article.objects.filter(featured=True).order_by('-date')
    serializer = ArticleListSerializer(articles, many=True)
    return Response({
        'count': articles.count(),
        'articles': serializer.data
    })


@api_view(['GET'])
def get_categories(request):
    """Get all categories with article counts"""
    categories = []
    
    # Add 'all' category
    total_count = Article.objects.count()
    categories.append({
        'id': 'all',
        'name': 'All Categories',
        'count': total_count
    })
    
    # Add individual categories
    for category_id, category_name in Article.CATEGORY_CHOICES:
        count = Article.objects.filter(category=category_id).count()
        categories.append({
            'id': category_id,
            'name': category_name,
            'count': count
        })
    
    return Response(categories)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_article(request):
    """Create new article (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can create articles'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = ArticleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_article(request, article_id):
    """Update article (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can update articles'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    article = get_object_or_404(Article, id=article_id)
    serializer = ArticleSerializer(article, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_article(request, article_id):
    """Delete article (admin only)"""
    if request.user.role != 'admin':
        return Response(
            {'error': 'Only admins can delete articles'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    article = get_object_or_404(Article, id=article_id)
    article.delete()
    return Response(
        {'message': 'Article deleted successfully'}, 
        status=status.HTTP_204_NO_CONTENT
    )


@api_view(['GET'])
def search_articles(request):
    """Search articles by query"""
    query = request.GET.get('q', '')
    if not query:
        return Response(
            {'error': 'Search query is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    articles = Article.objects.filter(
        Q(title__icontains=query) | 
        Q(excerpt__icontains=query) | 
        Q(content__icontains=query)
    ).order_by('-date')
    
    serializer = ArticleListSerializer(articles, many=True)
    return Response({
        'query': query,
        'count': articles.count(),
        'results': serializer.data
    })