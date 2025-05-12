from django.db import models
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from userApp.models import CustomUser
from professionalApp.models import Lawyer
from clientApp.models import Client
from speciliarizationApp.models import Specialization


class Case(models.Model):
    """
    Minimal model for legal cases submitted by clients and assigned to lawyers
    """
    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # Initial status when case is submitted
        ('assigned', 'Assigned'),  # When a lawyer is assigned
        ('in_progress', 'In Progress'),  # When lawyer begins working on the case
        ('completed', 'Completed'),  # When case is resolved
        ('rejected', 'Rejected'),  # When case is rejected
    ]
    
    # Case information
    title = models.CharField(max_length=200)
    case_number = models.CharField(max_length=50, unique=True, editable=False)
    description = models.TextField()
    
    # Relationships
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='cases'
    )
    lawyer = models.ForeignKey(
        Lawyer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cases'
    )
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases'
    )
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attachment = models.FileField(upload_to='case_attachments/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
    
    def __str__(self):
        return f"{self.case_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate a unique case number for new cases
        if not self.pk and not self.case_number:
            # Format: YEAR-MONTH-RANDOMSTRING
            import datetime
            
            today = datetime.date.today()
            random_str = get_random_string(length=6, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            self.case_number = f"{today.year}-{today.month:02d}-{random_str}"
        
        super().save(*args, **kwargs)