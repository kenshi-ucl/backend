from rest_framework import serializers
from .shop_models import Product, CartItem, Payment, Review
from .models import User
from django.contrib.auth import authenticate

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user_email', 'rating', 'comment', 'created_at']
        read_only_fields = ['user_email']

    def get_user_email(self, obj):
        return obj.user.email

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'image', 'image_url', 'created_at', 'updated_at', 'reviews', 'average_rating']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            # Manually construct the URL with the port
            base_url = "http://172.22.201.82:3000/kenshi"
            relative_url = instance.image.url
            representation['image'] = f"{base_url}{relative_url}"
        else:
            representation['image'] = None
        return representation

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return str(obj.quantity * obj.product.price)

class PaymentSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Payment
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.avatar:
            # Manually construct the URL with the port
            base_url = "http://172.22.201.82:3000/kenshi"
            relative_url = instance.avatar.url
            representation['avatar'] = f"{base_url}{relative_url}"
        else:
            representation['avatar'] = None
        return representation

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Invalid credentials')
