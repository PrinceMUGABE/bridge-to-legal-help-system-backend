# articles/models.py
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()


class Article(models.Model):
    CATEGORY_CHOICES = [
        ('family', 'Family Law'),
        ('criminal', 'Criminal Law'),
        ('business', 'Business Law'),
        ('property', 'Property Law'),
        ('employment', 'Employment Law'),
    ]
    
    title = models.CharField(max_length=255)
    excerpt = models.TextField()
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    author = models.CharField(max_length=100)  # Simple text field for author name
    date = models.DateTimeField(default=now)
    read_time = models.CharField(max_length=20, default='5 min read')
    views = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    image = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return self.title
    
    def get_category_display_name(self):
        """Get the display name for category"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)