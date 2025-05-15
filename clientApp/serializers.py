from rest_framework import serializers
from .models import Client
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
        
    def validate_date_of_birth(self, value):
        """
        Check that the date of birth is not in the future
        """
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        return value
    


class ClientProfileUpdateSerializer(serializers.Serializer):
    # CustomUser fields
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(max_length=10, required=True)
    
    # Client fields
    first_name = serializers.CharField(max_length=50, required=False)
    middle_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False)
    gender = serializers.CharField(max_length=10, required=False)
    date_of_birth = serializers.DateField(required=False)
    marital_status = serializers.CharField(max_length=20, required=False)
    province = serializers.CharField(max_length=100, required=False)
    district = serializers.CharField(max_length=100, required=False)
    sector = serializers.CharField(max_length=100, required=False)
    cell = serializers.CharField(max_length=100, required=False)
    village = serializers.CharField(max_length=100, required=False, allow_blank=True)
    education_level = serializers.CharField(max_length=20, required=False)
    national_id = serializers.CharField(max_length=16, required=False)
    
    def validate_date_of_birth(self, value):
        """
        Check that the date of birth is not in the future
        """
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        return value