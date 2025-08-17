from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string


from caseApp.models import Case
from clientApp.models import Client
from professionalApp.models import Lawyer
from .serializers import (
    CaseSerializer, 
    CaseCreateSerializer, 
    CaseUpdateSerializer,
    CaseStatusUpdateSerializer,
    ClientSerializer
)



def send_case_notification(case):
    """Helper function to send email notifications about a case"""
    # Get all recipients
    recipients = []
    
    # Add client email if available
    if case.client and case.client.user.email:
        recipients.append(case.client.user.email)
    
    # Add lawyer email if available
    if case.lawyer and case.lawyer.user.email:
        recipients.append(case.lawyer.user.email)
    
    # Add admins
    admin_emails = [
        admin.email for admin in 
        case.client.user.__class__.objects.filter(role='admin', is_active=True)
        if admin.email
    ]
    recipients.extend(admin_emails)
    
    # Prepare email content
    subject = f"Case Notification: {case.case_number}"
    context = {
        'case': case,
        'case_number': case.case_number,
        'title': case.title,
        'description': case.description,
        'status': case.status,
        'client_name': f"{case.client.first_name} {case.client.last_name}",
    }
    
    if case.lawyer:
        context['lawyer_name'] = f"{case.lawyer.first_name} {case.lawyer.last_name}"
    else:
        context['lawyer_name'] = "Not assigned yet"
    
    # Use the correct template path
    template_path = 'caseApp/case_notification_email.html'
    
    html_message = render_to_string(template_path, context)
    plain_message = f"""
    Case Number: {case.case_number}
    Title: {case.title}
    Status: {case.status}
    Description: {case.description}
    Client: {context['client_name']}
    Lawyer: {context['lawyer_name']}
    """
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_case(request):
    """Create a new case for the logged-in client"""
    user = request.user
    
    print(f"Submitted user creating case {user.id}, {user.email}")
    
    # Only customers can create cases for themselves
    if user.role != 'customer':
        print("Only clients can create cases for themselves.")
        return Response(
            {"error": "Only clients can create cases for themselves."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get the client instance for the current user
        client = Client.objects.get(user=user)
        
        # Check if client is active
        if client.status != 'active':
            print("Only active clients can create cases.")
            return Response(
                {"error": "Only active clients can create cases."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create serializer and validate
        data = request.data.copy()
        data['client'] = client.id

        serializer = CaseCreateSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                # Fix: Pass client instance directly during save instead of through data
                case = serializer.save()
                
                # Set initial status
                if 'lawyer' in request.data and request.data['lawyer']:
                    case.status = 'pending'
                    case.save()
                
                # Send notification emails
                send_case_notification(case)
                
                # Return the created case
                response_serializer = CaseSerializer(case)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Client.DoesNotExist:
        print("Client profile not found for this user.")
        return Response(
            {"error": "Client profile not found for this user."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
    
        print(f"Error creating case: {str(e)}")     
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_create_case(request):
    """Create a case as an admin, assigning it to a specific client and lawyer"""
    user = request.user
    
    # Only admins can use this endpoint
    if user.role != 'admin':
        return Response(
            {"error": "Only admins can create cases for other users."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Validate required fields
        if 'client' not in request.data:
            return Response(
                {"error": "Client ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CaseCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                case = serializer.save()
                
                # Set initial status
                if 'lawyer' in request.data and request.data['lawyer']:
                    case.status = 'assigned'
                    case.save()
                
                # Send notification emails
                send_case_notification(case)
                
                # Return the created case
                response_serializer = CaseSerializer(case)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lawyer_create_case(request):
    """Create a case as a lawyer, assigning it to a specific client"""
    user = request.user
    
    # Only lawyers can use this endpoint
    if user.role != 'lawyer':
        return Response(
            {"error": "Only lawyers can create cases."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get the lawyer profile for the current user
        try:
            lawyer = Lawyer.objects.get(user=user)
        except Lawyer.DoesNotExist:
            return Response(
                {"error": "Lawyer profile not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate required fields
        if 'client' not in request.data:
            return Response(
                {"error": "Client is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create a mutable copy of the request data
        data = request.data.copy()
        # Automatically assign the current lawyer to the case
        data['lawyer'] = lawyer.id
        
        serializer = CaseCreateSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                case = serializer.save()
                
                # Set initial status since we're assigning a lawyer
                case.status = 'assigned'
                case.save()
                
                # Send notification emails (implement this function as needed)
                send_case_notification(case)
                
                # Return the created case
                response_serializer = CaseSerializer(case)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_case_by_id(request, case_id):
    """Get a specific case by ID"""
    user = request.user
    
    try:
        # Get the case
        case = get_object_or_404(Case, id=case_id)
        
        # Check permissions based on user role
        if user.role == 'customer':
            # Clients can only view their own cases
            try:
                client = Client.objects.get(user=user)
                if case.client.id != client.id:
                    return Response(
                        {"error": "You do not have permission to view this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Client.DoesNotExist:
                return Response(
                    {"error": "Client profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif user.role == 'lawyer':
            # Lawyers can only view cases assigned to them
            try:
                lawyer = Lawyer.objects.get(user=user)
                if case.lawyer and case.lawyer.id != lawyer.id:
                    return Response(
                        {"error": "You do not have permission to view this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Lawyer.DoesNotExist:
                return Response(
                    {"error": "Lawyer profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Admins can view all cases
        
        serializer = CaseSerializer(case)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lawyer_partner_clients(request):
    """
    Get all clients that have cases assigned to the current lawyer
    """
    user = request.user
    
    # Only lawyers can access this endpoint
    if user.role != 'lawyer':
        return Response(
            {"error": "Only lawyers can access partner clients."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Get the lawyer profile for the current user
        try:
            lawyer = Lawyer.objects.get(user=user)
        except Lawyer.DoesNotExist:
            return Response(
                {"error": "Lawyer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all unique clients who have cases with this lawyer
        clients = Client.objects.filter(
            cases__lawyer=lawyer
        ).distinct()
        
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_client_cases(request):
    """Get all cases for the logged-in client"""
    user = request.user
    
    # Only clients can use this endpoint
    if user.role != 'customer':
        return Response(
            {"error": "Only clients can use this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        client = Client.objects.get(user=user)
        cases = Case.objects.filter(client=client)
        serializer = CaseSerializer(cases, many=True)
        return Response(serializer.data)
    
    except Client.DoesNotExist:
        return Response(
            {"error": "Client profile not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cases_by_client_id(request, client_id):
    """Get all cases for a specific client (admin only)"""
    user = request.user
    
    # Only admins can view cases for any client
    if user.role != 'admin':
        return Response(
            {"error": "Only admins can view cases for any client."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        client = get_object_or_404(Client, id=client_id)
        cases = Case.objects.filter(client=client)
        serializer = CaseSerializer(cases, many=True)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lawyer_cases(request):
    """Get all cases assigned to the logged-in lawyer"""
    user = request.user
    
    # Only lawyers can use this endpoint
    if user.role != 'lawyer':
        return Response(
            {"error": "Only lawyers can use this endpoint."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        lawyer = Lawyer.objects.get(user=user)
        cases = Case.objects.filter(lawyer=lawyer)
        serializer = CaseSerializer(cases, many=True)
        return Response(serializer.data)
    
    except Lawyer.DoesNotExist:
        return Response(
            {"error": "Lawyer profile not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_cases(request):
    """Get all cases (admin only)"""
    user = request.user
    
    # Only admins can view all cases
    if user.role != 'admin':
        return Response(
            {"error": "Only admins can view all cases."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        cases = Case.objects.all()
        serializer = CaseSerializer(cases, many=True)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cases_by_lawyer_id(request, lawyer_id):
    """Get all cases assigned to a specific lawyer (admin only)"""
    user = request.user
    
    # Only admins can view cases for any lawyer
    if user.role != 'admin':
        return Response(
            {"error": "Only admins can view cases for any lawyer."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        lawyer = get_object_or_404(Lawyer, id=lawyer_id)
        cases = Case.objects.filter(lawyer=lawyer)
        serializer = CaseSerializer(cases, many=True)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_case(request, case_id):
    """Update a case"""
    user = request.user
    
    try:
        case = get_object_or_404(Case, id=case_id)
        
        # Check permissions based on user role
        if user.role == 'customer':
            # Clients can only update their own cases
            try:
                client = Client.objects.get(user=user)
                if case.client.id != client.id:
                    return Response(
                        {"error": "You do not have permission to update this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Clients can only update specific fields
                allowed_fields = ['title', 'description', 'attachment']
                data = {k: v for k, v in request.data.items() if k in allowed_fields}
                
            except Client.DoesNotExist:
                return Response(
                    {"error": "Client profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif user.role == 'lawyer':
            # Lawyers can only update cases assigned to them
            try:
                lawyer = Lawyer.objects.get(user=user)
                if case.lawyer and case.lawyer.id != lawyer.id:
                    return Response(
                        {"error": "You do not have permission to update this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Lawyers can only update specific fields
                allowed_fields = ['status', 'description', 'attachment']
                data = {k: v for k, v in request.data.items() if k in allowed_fields}
                
            except Lawyer.DoesNotExist:
                return Response(
                    {"error": "Lawyer profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        else:  # Admin case
            data = request.data
        
        serializer = CaseUpdateSerializer(case, data=data, partial=True)
        if serializer.is_valid():
            updated_case = serializer.save()
            
            # Send notification email if significant changes
            if set(data.keys()) - {'attachment'}:
                send_case_notification(updated_case)
            
            response_serializer = CaseSerializer(updated_case)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_case(request, case_id):
    """Delete a case (admin only)"""
    user = request.user
    
    # Only admins can delete cases
    if user.role != 'admin':
        return Response(
            {"error": "Only admins can delete cases."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        case = get_object_or_404(Case, id=case_id)
        case_number = case.case_number  # Save for response
        
        # Delete the case
        case.delete()
        
        return Response(
            {"message": f"Case {case_number} has been deleted successfully."},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_case_status(request, case_id):
    """Update the status of a case"""
    user = request.user
    
    try:
        case = get_object_or_404(Case, id=case_id)
        
        # Check permissions based on user role
        if user.role == 'customer':
            # Clients can only update status for their own cases
            try:
                client = Client.objects.get(user=user)
                if case.client.id != client.id:
                    return Response(
                        {"error": "You do not have permission to update this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Clients can only set limited statuses
                allowed_statuses = ['completed']
                if request.data.get('status') not in allowed_statuses:
                    return Response(
                        {"error": f"Clients can only set these statuses: {', '.join(allowed_statuses)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            except Client.DoesNotExist:
                return Response(
                    {"error": "Client profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif user.role == 'lawyer':
            # Lawyers can only update status for cases assigned to them
            try:
                lawyer = Lawyer.objects.get(user=user)
                if case.lawyer and case.lawyer.id != lawyer.id:
                    return Response(
                        {"error": "You do not have permission to update this case."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Lawyers can only set certain statuses
                allowed_statuses = ['in_progress', 'completed']
                if request.data.get('status') not in allowed_statuses:
                    return Response(
                        {"error": f"Lawyers can only set these statuses: {', '.join(allowed_statuses)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            except Lawyer.DoesNotExist:
                return Response(
                    {"error": "Lawyer profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Admin can set any status
        
        serializer = CaseStatusUpdateSerializer(case, data=request.data, partial=True)
        if serializer.is_valid():
            updated_case = serializer.save()
            
            # Send notification email
            send_case_notification(updated_case)
            
            response_serializer = CaseSerializer(updated_case)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
        
        
        
        