from django.contrib import admin
from .models import Product, PriceHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'last_price', 'last_checked', 'created_at']
    search_fields = ['name', 'url']
    list_filter = ['created_at']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'price', 'recorded_at']
    list_filter = ['product', 'recorded_at']
