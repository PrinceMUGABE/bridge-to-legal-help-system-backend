from django.urls import path
from . import views

app_name = 'caseApp'

urlpatterns = [
    # Case creation endpoints
    path('create/', views.create_case, name='create_case'),  # For clients to create their own cases
    path('admin/create/', views.admin_create_case, name='admin_create_case'),  # For admins to create cases
    
    # Case retrieval endpoints
    path('<int:case_id>/', views.get_case_by_id, name='get_case_by_id'),  # Get a specific case
    path('cases/', views.get_all_cases, name='get_all_cases'),  # Get all cases (admin only)
    path('client/', views.get_client_cases, name='get_client_cases'),  # Get logged-in client's cases
    path('client/<int:client_id>/', views.get_cases_by_client_id, name='get_cases_by_client_id'),  # Get cases for specific client
    path('lawyer/', views.get_lawyer_cases, name='get_lawyer_cases'),  # Get logged-in lawyer's cases
    path('lawyer/<int:lawyer_id>/', views.get_cases_by_lawyer_id, name='get_cases_by_lawyer_id'),  # Get cases for specific lawyer
    
    # Case update endpoints
    path('update/<int:case_id>/', views.update_case, name='update_case'),  # Update a case
    path('status/<int:case_id>/', views.update_case_status, name='update_case_status'),  # Update case status
    
    # Case deletion endpoint
    path('delete/<int:case_id>/', views.delete_case, name='delete_case'),  # Delete a case (admin only)
]