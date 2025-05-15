from django.urls import path
from . import views


urlpatterns = [

    path('create/', views.create_client, name='create_client'),
    path('clients/', views.get_all_clients, name='get_all_clients'),
    path('<int:client_id>/', views.get_client_by_id, name='get_client_by_id'),
    path('update/<int:client_id>/', views.update_client, name='update_client'),
    path('delete/<int:client_id>/', views.delete_client, name='delete_client'),
    
    path('my-profile/', views.get_clients_created_by_user, name='get-client-profile'),
    path('update-profile/', views.update_client_profile, name='update-client-profile'),
]