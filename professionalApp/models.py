from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.crypto import get_random_string
from userApp.models import CustomUser
from speciliarizationApp.models import Specialization


class Lawyer(models.Model):
    """
    Extended profile for users with the 'lawyer' role
    """
    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    # Availability status choices
    AVAILABILITY_CHOICES = [
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
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ]
    
    # Personal information
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='lawyer',
        limit_choices_to={'role': 'lawyer'}
    )
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    
    # Location information
    residence_district = models.CharField(max_length=100)
    residence_sector = models.CharField(max_length=100)
    
    # Professional information
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES)
    diploma = models.FileField(upload_to='lawyer_diplomas/', blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    
    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='inactive')
    
    # Metadata
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='lawyer_created_by'
    )
    
    specializations = models.ManyToManyField(
        Specialization,
        related_name='lawyer_specializations'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.phone_number})"
  
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lawyer'
        verbose_name_plural = 'Lawyers'
        
    def save(self, *args, **kwargs):
        # Set the initial status to pending for new lawyers
        if not self.pk:
            self.status = 'pending'
        super().save(*args, **kwargs)