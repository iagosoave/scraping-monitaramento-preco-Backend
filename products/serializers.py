from rest_framework import serializers
from .models import Product, PriceHistory


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'price', 'recorded_at']


class ProductSerializer(serializers.ModelSerializer):
    price_history = PriceHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'url', 'last_price', 'last_checked', 'created_at', 'updated_at', 'price_history']
        read_only_fields = ['id', 'last_price', 'last_checked', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'url']
        read_only_fields = ['id']

    def validate_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL deve começar com http:// ou https://")
        return value
