from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from .shop_models import Product, CartItem, Payment  # Add this import
from .shop_serializers import ProductSerializer, CartItemSerializer, PaymentSerializer  # Add this import

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        print("Debug - Serialized data:", data)  # Debug output
        return Response(data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        try:
            product = self.get_object()
            new_stock = request.data.get('stock')
            if new_stock is not None:
                product.stock = int(new_stock)
                product.save()
                return Response({'status': 'stock updated', 'new_stock': product.stock})
            return Response({'error': 'stock value required'}, status=400)
        except Product.DoesNotExist:
            return Response({'error': 'product not found'}, status=404)
        except ValueError:
            return Response({'error': 'invalid stock value'}, status=400)

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def create(self, request, *args, **kwargs):
        try:
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity', 1)
            
            # Validate product exists
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'detail': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check stock availability
            if product.stock < quantity:
                return Response(
                    {'detail': 'Not enough stock available'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create or update cart item
            cart_item, created = CartItem.objects.get_or_create(
                product=product,
                user=request.user,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            # Update product stock
            product.stock -= quantity
            product.save()

            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            cart_item = self.get_object()
            new_quantity = request.data.get('quantity')
            
            if new_quantity is None:
                return Response(
                    {'detail': 'Quantity is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate quantity difference
            quantity_diff = new_quantity - cart_item.quantity
            
            # Check if enough stock is available
            if quantity_diff > 0 and cart_item.product.stock < quantity_diff:
                return Response(
                    {'detail': 'Not enough stock available'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update product stock
            cart_item.product.stock -= quantity_diff
            cart_item.product.save()

            # Update cart item quantity
            cart_item.quantity = new_quantity
            cart_item.save()

            serializer = self.get_serializer(cart_item)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            cart_item = self.get_object()
            
            # Restore product stock
            cart_item.product.stock += cart_item.quantity
            cart_item.product.save()

            # Delete cart item
            cart_item.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    http_method_names = ['get', 'post', 'head']

    @action(detail=False, methods=['post'], url_path='process')
    def process_payment(self, request):
        try:
            with transaction.atomic():
                # Validate and process products data
                products_data = request.data.get('products', [])
                if not products_data:
                    return Response(
                        {'detail': 'No products selected for payment'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Handle multipart form data for file upload
                payment_data = {
                    'name': request.data.get('name'),
                    'email': request.data.get('email'),
                    'address': request.data.get('address'),
                    'payment_method': request.data.get('payment_method'),
                    'total_amount': request.data.get('total_amount'),
                    'products': products_data
                }

                # Handle avatar upload if present
                if 'avatar' in request.FILES:
                    payment_data['avatar'] = request.FILES['avatar']

                serializer = self.get_serializer(data=payment_data)
                serializer.is_valid(raise_exception=True)
                payment = serializer.save()

                # Process cart items and update stock
                cart_items = request.data.get('cart_items', [])
                if cart_items:
                    cart_items_queryset = CartItem.objects.filter(id__in=cart_items)
                    
                    # Update product stock
                    for cart_item in cart_items_queryset:
                        product = cart_item.product
                        if product.stock < cart_item.quantity:
                            raise ValueError(f"Not enough stock for {product.name}")
                        
                        product.stock -= cart_item.quantity
                        product.save()

                    # Clear cart items after successful stock update
                    cart_items_queryset.delete()

                return Response({
                    'order_id': payment.id,
                    'status': 'success',
                    'message': 'Payment processed successfully',
                    'data': {
                        'products': serializer.data.get('products', []),
                        'avatar': serializer.data.get('avatar'),
                        'name': serializer.data.get('name'),
                        'email': serializer.data.get('email'),
                        'address': serializer.data.get('address'),
                        'payment_method': serializer.data.get('payment_method'),
                        'total_amount': serializer.data.get('total_amount'),
                        'created_at': serializer.data.get('created_at')
                    }
                }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Include more detailed error information
            error_detail = str(e)
            if hasattr(e, 'detail'):
                error_detail = e.detail
            return Response(
                {'detail': error_detail},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('latest') == 'true':
            return queryset.order_by('-created_at')[:1]
        return queryset.order_by('-created_at')