from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Feedback
from .serializers import FeedbackSerializer
from caseApp.models import Case
from clientApp.models import Client
from professionalApp.models import Lawyer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_feedback(request):
    """ Create a new feedback entry with proper error handling """
    try:
        data = request.data.copy()
        
        # Validate required fields
        if 'case' not in data:
            print("Error: Missing required field 'case'")
            return Response(
                {"error": "Missing required field", "message": "case ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if 'rating' not in data:
            print("Error: Missing required field 'rating'")
            return Response(
                {"error": "Missing required field", "message": "Rating is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate and convert rate to integer
        if 'rate' in data:
            try:
                data['rate'] = int(data['rate'])
            except (ValueError, TypeError):
                print(f"Error: Invalid rate value '{data['rate']}', must be an integer")
                return Response(
                    {"error": "Invalid data", "message": "Rate must be a valid integer"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Validate and convert rating to integer
        try:
            data['rating'] = int(data['rating'])
            if data['rating'] < 1 or data['rating'] > 5:
                print(f"Error: Rating value {data['rating']} out of range (1-5)")
                return Response(
                    {"error": "Invalid data", "message": "Rating must be between 1 and 5"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            print(f"Error: Invalid rating value '{data['rating']}', must be an integer")
            return Response(
                {"error": "Invalid data", "message": "Rating must be a valid integer between 1 and 5"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate case exists
        try:
            case_id = int(data['case'])
            case = Case.objects.get(id=case_id)
            data['case'] = case_id
        except (ValueError, TypeError):
            print(f"Error: Invalid case ID '{data['case']}', must be an integer")
            return Response(
                {"error": "Invalid data", "message": "case ID must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except case.DoesNotExist:
            print(f"Error: case with ID {data['case']} not found")
            return Response(
                {"error": "Not found", "message": f"case with ID {data['case']} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Add the current user as creator
        data["created_by"] = request.user.id
        
        # Create feedback
        serializer = FeedbackSerializer(data=data)
        if serializer.is_valid():
            serializer.save(created_by=request.user, case=case)
            print(f"Success: Feedback created for case {case_id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"Error: Serializer validation failed - {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print(f"Unexpected error during feedback creation: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_all_feedbacks(request):
    """ Retrieve all feedback entries """
    try:
        feedbacks = Feedback.objects.all()
        serializer = FeedbackSerializer(feedbacks, many=True)
        
        print(f"Feddbacks data: {serializer.data}\n\n")
        return Response(serializer.data)
    except Exception as e:
        print(f"Error retrieving all feedbacks: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_feedback_by_id(request, feedback_id):
    """ Retrieve a single feedback by ID """
    try:
        try:
            feedback_id = int(feedback_id)
        except (ValueError, TypeError):
            print(f"Error: Invalid feedback ID '{feedback_id}', must be an integer")
            return Response(
                {"error": "Invalid ID", "message": "Feedback ID must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            serializer = FeedbackSerializer(feedback)
            return Response(serializer.data)
        except Feedback.DoesNotExist:
            print(f"Error: Feedback with ID {feedback_id} not found")
            return Response(
                {"error": "Not found", "message": f"Feedback with ID {feedback_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        print(f"Error retrieving feedback by ID: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def update_feedback(request, feedback_id):
    """ Update a feedback entry """
    try:
        try:
            feedback_id = int(feedback_id)
        except (ValueError, TypeError):
            print(f"Error: Invalid feedback ID '{feedback_id}', must be an integer")
            return Response(
                {"error": "Invalid ID", "message": "Feedback ID must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Find the feedback and check permissions
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            if feedback.created_by != request.user and not request.user.is_staff:
                print(f"Error: User {request.user.phone_number} does not have permission to update feedback {feedback_id}")
                return Response(
                    {"error": "Permission denied", "message": "You can only update your own feedback"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Feedback.DoesNotExist:
            print(f"Error: Feedback with ID {feedback_id} not found")
            return Response(
                {"error": "Not found", "message": f"Feedback with ID {feedback_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        data = request.data.copy()
        
        # Handle rate conversion if present
        if 'rate' in data:
            try:
                data['rate'] = int(data['rate'])
            except (ValueError, TypeError):
                print(f"Error: Invalid rate value '{data['rate']}', must be an integer")
                return Response(
                    {"error": "Invalid data", "message": "Rate must be a valid integer"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Handle rating conversion if present
        if 'rating' in data:
            try:
                data['rating'] = int(data['rating'])
                if data['rating'] < 1 or data['rating'] > 5:
                    print(f"Error: Rating value {data['rating']} out of range (1-5)")
                    return Response(
                        {"error": "Invalid data", "message": "Rating must be between 1 and 5"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                print(f"Error: Invalid rating value '{data['rating']}', must be an integer")
                return Response(
                    {"error": "Invalid data", "message": "Rating must be a valid integer between 1 and 5"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Handle case ID if present
        if 'case' in data:
            try:
                case_id = int(data['case'])
                case = Case.objects.get(id=case_id)
                data['case'] = case_id
            except (ValueError, TypeError):
                print(f"Error: Invalid case ID '{data['case']}', must be an integer")
                return Response(
                    {"error": "Invalid data", "message": "case ID must be a valid integer"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except case.DoesNotExist:
                print(f"Error: case with ID {data['case']} not found")
                return Response(
                    {"error": "Not found", "message": f"case with ID {data['case']} not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Update feedback
        serializer = FeedbackSerializer(feedback, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(f"Success: Feedback {feedback_id} updated")
            return Response(serializer.data)
            
        print(f"Error: Serializer validation failed - {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"Unexpected error during feedback update: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_feedback(request, feedback_id):
    """ Delete a feedback entry """
    try:
        try:
            feedback_id = int(feedback_id)
        except (ValueError, TypeError):
            print(f"Error: Invalid feedback ID '{feedback_id}', must be an integer")
            return Response(
                {"error": "Invalid ID", "message": "Feedback ID must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Find the feedback and check permissions
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            if feedback.created_by != request.user and not request.user.is_staff:
                print(f"Error: User {request.user.phone_number} does not have permission to delete feedback {feedback_id}")
                return Response(
                    {"error": "Permission denied", "message": "You can only delete your own feedback"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Feedback.DoesNotExist:
            print(f"Error: Feedback with ID {feedback_id} not found")
            return Response(
                {"error": "Not found", "message": f"Feedback with ID {feedback_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Delete feedback
        feedback.delete()
        print(f"Success: Feedback {feedback_id} deleted")
        return Response({"message": "Feedback deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        print(f"Unexpected error during feedback deletion: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_feedbacks_by_logged_in_user(request):
    """ Retrieve feedbacks created by the logged-in user """
    try:
        feedbacks = Feedback.objects.filter(created_by=request.user)
        serializer = FeedbackSerializer(feedbacks, many=True)
        print(f"Retrieved {len(feedbacks)} feedbacks for user {request.user.phone_number}")
        return Response(serializer.data)
    except Exception as e:
        print(f"Error retrieving user feedbacks: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feedbacks_for_client_cases(request):
    """ 
    Retrieve all feedbacks for cases associated with the logged-in client 
    
    This view does the following:
    1. Checks if the logged-in user is a client
    2. Finds all cases associated with the client
    3. Retrieves all feedbacks for those cases
    4. Returns the feedbacks as a JSON response
    """
    try:
        # Try to get the client profile for the logged-in user
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return Response(
                {"error": "User is not a registered client"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all cases for this client
        client_cases = Case.objects.filter(client=client)
        
        # Retrieve feedbacks for these cases
        feedbacks = Feedback.objects.filter(case__in=client_cases)
        
        # Serialize the feedbacks
        serializer = FeedbackSerializer(feedbacks, many=True)
        
        # Log the number of feedbacks retrieved
        print(f"Retrieved {len(feedbacks)} feedbacks for client {client.first_name} {client.last_name}")
        
        return Response(serializer.data)
    
    except Exception as e:
        # Log any unexpected errors
        print(f"Error retrieving client case feedbacks: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feedbacks_for_lawyer_cases(request):
    """ 
    Retrieve all feedbacks for cases associated with the logged-in client 
    
    This view does the following:
    1. Checks if the logged-in user is a client
    2. Finds all cases associated with the client
    3. Retrieves all feedbacks for those cases
    4. Returns the feedbacks as a JSON response
    """
    try:
        # Try to get the client profile for the logged-in user
        try:
            lawyer = Lawyer.objects.get(user=request.user)
        except Lawyer.DoesNotExist:
            return Response(
                {"error": "User is not a registered lawyer"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all cases for this client
        lawyer_cases = Case.objects.filter(lawyer=lawyer)
        
        # Retrieve feedbacks for these cases
        feedbacks = Feedback.objects.filter(case__in=lawyer_cases)
        
        # Serialize the feedbacks
        serializer = FeedbackSerializer(feedbacks, many=True)
        
        # Log the number of feedbacks retrieved
        print(f"Retrieved {len(feedbacks)} feedbacks for lawyer {lawyer.first_name} {lawyer.last_name}")
        
        return Response(serializer.data)
    
    except Exception as e:
        # Log any unexpected errors
        print(f"Error retrieving lawyer case feedbacks: {str(e)}")
        return Response(
            {"error": "Server error", "message": f"An unexpected error occurred: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )