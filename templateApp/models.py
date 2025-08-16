from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Template(models.Model):
    CATEGORY_CHOICES = [
        ('employment-law', 'Employment Law'),
        ('property-law', 'Property Law'),
        ('business-law', 'Business Law'),
        ('family-law', 'Family Law'),
        ('estate-law', 'Estate Law'),
        ('general', 'General'),
        ('consumer-law', 'Consumer Law'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('DOCX', 'DOCX'),
    ]
    
    PRICE_CHOICES = [
        ('Free', 'Free'),
        ('Premium', 'Premium'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    description = models.TextField()
    downloads = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=2, 
        decimal_places=1, 
        default=Decimal('0.0'),  # Changed from 0.0 to Decimal('0.0')
        validators=[MinValueValidator(Decimal('0.0')), MaxValueValidator(Decimal('5.0'))]  # Changed to Decimal objects
    )
    author = models.CharField(max_length=100)
    preview = models.BooleanField(default=True)
    price = models.CharField(max_length=10, choices=PRICE_CHOICES, default='Free')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File upload field for the actual template
    template_file = models.FileField(upload_to='templates/', null=True, blank=True)
    
    class Meta:
        ordering = ['-downloads', '-rating', '-created_at']
        verbose_name = "Template"
        verbose_name_plural = "Templates"
    
    def __str__(self):
        return self.title
    
    def get_category_display_name(self):
        """Get the display name for category"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)
    
    def get_last_updated(self):
        """Return formatted last updated date"""
        return self.updated_at.strftime('%Y-%m-%d')
    
    def increment_downloads(self):
        """Increment download count"""
        self.downloads += 1
        self.save(update_fields=['downloads'])