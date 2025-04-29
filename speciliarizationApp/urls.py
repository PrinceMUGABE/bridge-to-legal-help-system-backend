from django.urls import path
from .views import *

urlpatterns = [
    path('create/', create_specialization, name='create_specialization'),
    path('get_all/', get_all_specializations, name='get_all_specializations'),
    path('<int:id>/', get_specialization_by_id, name='get_specialization'),
    path('update/<int:id>/', update_specialization, name='update_specialization'),
    path('delete/<int:id>/', delete_specialization, name='delete_specialization'),
    path('status/<str:status>/', get_specialization_by_status, name='get_specialization_by_name'),
    path('get_by_user/', get_user_specializations, name='get_specialization_by_user'),
    
]
