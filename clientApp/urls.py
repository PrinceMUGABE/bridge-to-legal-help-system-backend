from django.urls import path
from . import views


urlpatterns = [

    path('create/', views.create_client, name='create_client'),
    path('clients/', views.get_all_clients, name='get_all_clients'),
    path('<int:client_id>/', views.get_client_by_id, name='get_client_by_id'),
    path('user/', views.get_clients_created_by_user, name='get_clients_created_by_user'),
    path('update/<int:client_id>/', views.update_client, name='update_client'),
    path('delete/<int:client_id>/', views.delete_client, name='delete_client'),
]