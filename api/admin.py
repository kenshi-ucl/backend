from django.contrib import admin
from .models import User
from .shop_models import Product, CartItem, Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Payment)
