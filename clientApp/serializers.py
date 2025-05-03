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