from rest_framework import serializers
from caseApp.models import Case
from clientApp.models import Client
from professionalApp.models import Lawyer
from speciliarizationApp.models import Specialization
from django.core.exceptions import ValidationError
from userApp.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'email', 'role', 'created_at']
        
        
class ClientSerializer(serializers.ModelSerializer):
    """
    Main serializer for Client model with user information included
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'user')
        
        
        
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
    
            
    
class CaseSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    lawyer = LawyerSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)
    class Meta:
        model = Case
        fields = [
            'id', 'title', 'case_number', 'description', 'client', 'lawyer',
            'specialization', 'status', 'attachment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['case_number', 'created_at', 'updated_at']
        
    def validate(self, data):
        # Validate client is active
        if 'client' in data:
            client = data['client']
            if client.status != 'active':
                raise serializers.ValidationError({"client": "Only active clients can be associated with cases."})
        
        # Validate lawyer is accepted
        if 'lawyer' in data:
            lawyer = data['lawyer']
            if lawyer.status != 'accepted':
                raise serializers.ValidationError({"lawyer": "Only accepted lawyers can be assigned to cases."})
            
            # Check if lawyer is available
            if lawyer.availability_status != 'active':
                raise serializers.ValidationError({"lawyer": "This lawyer is currently not available for new cases."})
        
        return data


class CaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            'title', 'description', 'client', 'lawyer',
            'specialization', 'attachment'
        ]

    def validate(self, data):
        # Validate client is active
        if 'client' in data:
            client = data['client']
            if client.status != 'active':
                raise serializers.ValidationError({"client": "Only active clients can be associated with cases."})
        
        # Validate lawyer is accepted
        if 'lawyer' in data:
            lawyer = data['lawyer']
            if lawyer.status != 'accepted':
                raise serializers.ValidationError({"lawyer": "Only accepted lawyers can be assigned to cases."})
            
            # Check if lawyer is available
            if lawyer.availability_status != 'active':
                raise serializers.ValidationError({"lawyer": "This lawyer is currently not available for new cases."})
        
        return data


class CaseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            'title', 'description', 'lawyer',
            'specialization', 'attachment'
        ]
        
    def validate(self, data):
        # Validate lawyer is accepted
        if 'lawyer' in data:
            lawyer = data['lawyer']
            if lawyer.status != 'accepted':
                raise serializers.ValidationError({"lawyer": "Only accepted lawyers can be assigned to cases."})
            
            # Check if lawyer is available
            if lawyer.availability_status != 'active':
                raise serializers.ValidationError({"lawyer": "This lawyer is currently not available for new cases."})
        
        return data


class CaseStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ['status']
        
    def validate_status(self, value):
        valid_statuses = [status[0] for status in Case.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Choose from: {', '.join(valid_statuses)}")
        return value