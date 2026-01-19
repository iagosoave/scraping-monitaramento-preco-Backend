import threading
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Product, PriceHistory
from .serializers import ProductSerializer, ProductCreateSerializer, PriceHistorySerializer


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

        if request.data.get('start_scraping', False):
            def do_scrape():
                from products.tasks import scrape_product_price
                scrape_product_price(product.id)
            threading.Thread(target=do_scrape).start()

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def scrape(self, request, pk=None):
        product = self.get_object()

        def do_scrape():
            from products.tasks import scrape_product_price
            scrape_product_price(product.id)

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
