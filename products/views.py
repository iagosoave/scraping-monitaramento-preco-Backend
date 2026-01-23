import threading
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Product, PriceHistory
from .serializers import ProductSerializer, ProductCreateSerializer, PriceHistorySerializer
from .scraper import scrape_price
from django.utils import timezone


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['last_price']
    search_fields = ['name', 'url']
    ordering_fields = ['name', 'last_price', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        price = scrape_price(product.url)
        
        if price:
            product.last_price = price
            product.last_checked = timezone.now()
            product.save()
            
            PriceHistory.objects.create(product=product, price=price)

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def scrape(self, request, pk=None):
        product = self.get_object()

        def do_scrape():
            from .scraper import scrape_price
            from django.utils import timezone
            
            price = scrape_price(product.url)
            if price:
                product.last_price = price
                product.last_checked = timezone.now()
                product.save()
                PriceHistory.objects.create(product=product, price=price)

        threading.Thread(target=do_scrape).start()

        return Response({'message': f'Scraping iniciado para "{product.name}"'})

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        product = self.get_object()
        serializer = PriceHistorySerializer(product.price_history.all(), many=True)
        return Response(serializer.data)


class PriceHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PriceHistory.objects.all()
    serializer_class = PriceHistorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product']
    ordering_fields = ['price', 'recorded_at']