from rest_framework import serializers
from .models import Lawyer
from userApp.models import CustomUser
from speciliarizationApp.models import Specialization

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'created_at']

class SpecializationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']

class LawyerSerializer(serializers.ModelSerializer):
    """
    Main serializer for Lawyer model - handles all operations
    """
    user = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    specializations = SpecializationSerializer(many=True, read_only=True)
    
    
    
    # Fields for computed values used in list view
    user_phone = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    
    class Meta:
        model = Lawyer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_user_phone(self, obj):
        return obj.user.phone_number if obj.user else None
    

    
    def get_full_name(self, obj):
        middle = f" {obj.middle_name}" if obj.middle_name else ""
        return f"{obj.first_name}{middle} {obj.last_name}"