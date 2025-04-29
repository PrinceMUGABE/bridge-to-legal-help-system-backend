# Serializer
from rest_framework import serializers
from userApp.models import CustomUser
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Specialization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'created_at']

class SpecializationSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def get_created_by(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'phone_number': obj.created_by.phone_number,
                'role': obj.created_by.role
            }
        return None
    
    def validate_name(self, value):
        # Custom validation for name field
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long")
        
        # Check for existing name case-insensitive (on create or when name is changed)
        instance = self.instance
        if instance:
            # This is an update - check if name is changed
            if instance.name.lower() != value.lower():
                if Specialization.objects.filter(name__iexact=value).exists():
                    raise serializers.ValidationError("A specialization with this name already exists")
        else:
            # This is a create operation
            if Specialization.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("A specialization with this name already exists")
        
        return value