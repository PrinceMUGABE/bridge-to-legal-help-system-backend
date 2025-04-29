
from django.db import models
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from userApp.models import CustomUser

# Updated Model with created_by field
class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='specializations'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']