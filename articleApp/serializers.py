# articles/serializers.py
from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'excerpt', 'content', 'category', 'category_name',
            'author', 'date', 'read_time', 'views', 'featured', 'image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['views', 'created_at', 'updated_at']
    
    def get_category_name(self, obj):
        return obj.get_category_display_name()


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for listing articles (without content field)"""
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'excerpt', 'category', 'category_name',
            'author', 'date', 'read_time', 'views', 'featured', 'image'
        ]
    
    def get_category_name(self, obj):
        return obj.get_category_display_name()