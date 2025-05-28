from django.db import models
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(models.Model):
    name = models.CharField(max_length=100, default="Unnamed Product")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='Main_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),
            'stock': self.stock,
            'image': self.image.url if self.image else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'average_rating': self.average_rating
        }

    class Meta:
        verbose_name_plural = "Products"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')  # One review per product per user
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}'s review of {self.product.name}"

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CartItem: {self.quantity}x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

    def to_dict(self):
        """Convert cart item instance to dictionary for API responses"""
        return {
            'id': self.id,
            'quantity': self.quantity,
            'total_price': str(self.total_price),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'product': self.product.to_dict()  # Include all product details
        }

class Payment(models.Model):
    PAYMENT_CHOICES = [
        ('COD', 'Cash on delivery'),
        ('Gcash', 'Gcash'),
        ('PayMaya', 'PayMaya'),
        ('PayPal', 'PayPal')
    ]

    name = models.CharField(max_length=100, default="Anonymous")
    email = models.EmailField()
    address = models.TextField()
    avatar = models.ImageField(upload_to='Product_images/', null=True, blank=True)  # Add this line
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment by {self.name} via {self.payment_method}"

    def to_dict(self):
        """Convert payment instance to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'address': self.address,
            'avatar': self.avatar.url if self.avatar else None,  # Add this line
            'payment_method': self.payment_method,
            'total_amount': str(self.total_amount),
            'products': self.products,
            'created_at': self.created_at.isoformat()
        }