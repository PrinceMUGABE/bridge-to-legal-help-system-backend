# faq/serializers.py
from rest_framework import serializers
from .models import FAQ


class FAQSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'category', 'category_name',
            'popular', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_category_name(self, obj):
        return obj.get_category_display_name()