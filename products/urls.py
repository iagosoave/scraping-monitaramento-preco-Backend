from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, PriceHistoryViewSet

router = DefaultRouter()
router.register('products', ProductViewSet)
router.register('history', PriceHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
