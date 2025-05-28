from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .shop_serializers import UserSerializer, LoginSerializer, ReviewSerializer
from .models import User, Order
from .shop_models import Product, CartItem, Payment, Review
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class RegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({
            "message": "Please send a POST request with email, first_name, last_name, and password to register.",
            "required_fields": {
                "email": "string",
                "first_name": "string",
                "last_name": "string",
                "password": "string"
            }
        })

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            data = UserSerializer(user).data
            data.pop('password', None)
            data['token'] = str(refresh.access_token)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return Response({
            "message": "Please send a POST request with email and password to login.",
            "required_fields": {
                "email": "string",
                "password": "string"
            }
        })

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            data = UserSerializer(user).data
            data.pop('password', None)
            data['token'] = str(refresh.access_token)
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
            # Get total orders and spent amount
            orders = Order.objects.filter(user=user)
            total_orders = orders.count()
            total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
            
            # Get cart items count using the correct related name
            cart_items = CartItem.objects.filter(user=user).count()
            
            logger.debug(f"User stats - Orders: {total_orders}, Spent: {total_spent}, Cart Items: {cart_items}")
            
            return Response({
                'totalOrders': total_orders,
                'totalSpent': float(total_spent),
                'cartItems': cart_items
            })
        except Exception as e:
            logger.error(f"Error in UserStatsView: {str(e)}")
            return Response({
                'error': 'Failed to fetch user statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            
            # Get recent orders
            orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
            order_activities = [{
                'id': order.id,
                'type': 'order',
                'title': f'Order #{order.id}',
                'description': f'Ordered {order.items.count()} items for ${order.total_amount}',
                'date': order.created_at
            } for order in orders]
            
            # Get recent cart activities using the correct related name
            cart_activities = CartItem.objects.filter(user=user).order_by('-created_at')[:5]
            cart_activities = [{
                'id': f'cart_{item.id}',
                'type': 'cart',
                'title': 'Added to Cart',
                'description': f'Added {item.quantity}x {item.product.name} to cart',
                'date': item.created_at
            } for item in cart_activities]
            
            # Combine and sort activities
            all_activities = order_activities + cart_activities
            all_activities.sort(key=lambda x: x['date'], reverse=True)
            
            logger.debug(f"User activities - Orders: {len(order_activities)}, Cart: {len(cart_activities)}")
            
            return Response(all_activities[:10])  # Return top 10 most recent activities
        except Exception as e:
            logger.error(f"Error in UserActivityView: {str(e)}")
            return Response({
                'error': 'Failed to fetch user activities'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Check if user has already reviewed this product
            existing_review = Review.objects.filter(user=request.user, product=product).first()
            if existing_review:
                return Response({
                    'error': 'You have already reviewed this product'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new review
            review_data = {
                'product': product,
                'user': request.user,
                'rating': request.data.get('rating'),
                'comment': request.data.get('comment')
            }
            
            review = Review.objects.create(**review_data)
            serializer = ReviewSerializer(review)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            return Response({
                'error': 'Failed to create review'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, product_id):
        try:
            review = get_object_or_404(Review, product_id=product_id, user=request.user)
            
            # Update review
            review.rating = request.data.get('rating', review.rating)
            review.comment = request.data.get('comment', review.comment)
            review.save()
            
            serializer = ReviewSerializer(review)
            return Response(serializer.data)
            
        except Review.DoesNotExist:
            return Response({
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating review: {str(e)}")
            return Response({
                'error': 'Failed to update review'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, product_id):
        try:
            review = get_object_or_404(Review, product_id=product_id, user=request.user)
            review.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Review.DoesNotExist:
            return Response({
                'error': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting review: {str(e)}")
            return Response({
                'error': 'Failed to delete review'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
