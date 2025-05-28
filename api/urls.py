from django.urls import path
from .views import (
    RegisterView, LoginView, UserStatsView, UserActivityView,
    UpdateProfileView, ProductReviewView
)
from .shop_views import ProductViewSet, CartItemViewSet, PaymentViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'shop/products', ProductViewSet)
router.register(r'shop/cart', CartItemViewSet)
router.register(r'shop/payments', PaymentViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),
    path('user-activity/', UserActivityView.as_view(), name='user-activity'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('products/<int:product_id>/review/', ProductReviewView.as_view(), name='product-review'),
] + router.urls 