# faq/models.py
from django.db import models
from django.utils.timezone import now


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('getting-started', 'Getting Started'),
        ('legal-services', 'Legal Services'),
        ('billing', 'Billing & Payments'),
        ('lawyers', 'Finding Lawyers'),
        ('technical', 'Technical Support'),
    ]
    
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['popular', '-created_at']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question
    
    def get_category_display_name(self):
        """Get the display name for category"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)