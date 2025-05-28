from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import action
from .shop_views import ProductViewSet, CartItemViewSet, PaymentViewSet
from .views import RegisterView, LoginView, RegisterView, LoginView, UserStatsView, UserActivityView, UpdateProfileView, ProductReviewView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'cart-items', CartItemViewSet)
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('payments/process/', PaymentViewSet.as_view({
        'post': 'process_payment'
    }), name='payment-process'),
    path('shop/register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),
    path('user-activity/', UserActivityView.as_view(), name='user-activity'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('products/<int:product_id>/review/', ProductReviewView.as_view(), name='product-review'),
]   