from django.db import models
from django.utils.timezone import now
from userApp.models import CustomUser

class Client(models.Model):
    """
    Extended profile for users with the 'customer' role to store client/citizen information
    """
    # Status choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    # Gender choices
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    # Marital status choices
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    # Education level choices
    EDUCATION_LEVEL_CHOICES = [
        ('none', 'None'),
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ]
    
    # Personal information
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='client',
        limit_choices_to={'role': 'customer'}
    )
    first_name = models.CharField(max_length=50, default='')
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, default='')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    
    # Location information
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    cell = models.CharField(max_length=100)
    village = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional information
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES)

    
    # Identification
    national_id = models.CharField(max_length=16, unique=True)
    national_id_card = models.FileField(upload_to='client_national_cards/', blank=True, null=True)
    
    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    
    # Metadata
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone_number})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        
    def save(self, *args, **kwargs):
        # Ensure the linked user has the correct role
        if self.user.role != 'customer':
            raise ValueError("The linked user must have the 'customer' role")
        super().save(*args, **kwargs)