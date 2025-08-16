from rest_framework import serializers
from .models import Template
from decimal import Decimal


class TemplateSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display_name', read_only=True)
    last_updated = serializers.CharField(source='get_last_updated', read_only=True)
    template_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Template
        fields = [
            'id',
            'title',
            'category',
            'category_display',
            'format',
            'description',
            'downloads',
            'rating',
            'author',
            'preview',
            'price',
            'is_active',
            'last_updated',
            'template_file',
            'template_file_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['downloads', 'created_at', 'updated_at']
    
    def get_template_file_url(self, obj):
        """Return the full URL of the template file if it exists"""
        if obj.template_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.template_file.url)
            return obj.template_file.url
        return None


class TemplateCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating templates"""
    
    class Meta:
        model = Template
        fields = [
            'title',
            'category',
            'format',
            'description',
            'rating',
            'author',
            'preview',
            'price',
            'is_active',
            'template_file'
        ]
    
    def validate_rating(self, value):
        """Validate rating is between 0 and 5"""
        # Convert to Decimal if it's not already
        if not isinstance(value, Decimal):
            try:
                value = Decimal(str(value))
            except (ValueError, TypeError):
                raise serializers.ValidationError("Rating must be a valid number")
        
        if value < Decimal('0') or value > Decimal('5'):
            raise serializers.ValidationError("Rating must be between 0 and 5")
        return value
    
    def validate_title(self, value):
        """Validate title is not empty and unique"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        
        # Check for uniqueness during update
        if self.instance:
            if Template.objects.filter(title=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A template with this title already exists")
        else:
            if Template.objects.filter(title=value).exists():
                raise serializers.ValidationError("A template with this title already exists")
        
        return value
    
    def create(self, validated_data):
        """Override create to ensure is_active defaults to True if not provided"""
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True
        return super().create(validated_data)

class TemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing templates"""
    category_display = serializers.CharField(source='get_category_display_name', read_only=True)
    last_updated = serializers.CharField(source='get_last_updated', read_only=True)
    
    class Meta:
        model = Template
        fields = [
            'id',
            'title',
            'category',
            'category_display',
            'format',
            'description',
            'downloads',
            'rating',
            'author',
            'price',
            'last_updated'
        ]