from django.utils import timezone
from .models import Product, PriceHistory
from .scraper import scrape_price

try:
    from celery import shared_task
except ImportError:
    def shared_task(*args, **kwargs):
        def decorator(func):
            func.delay = lambda *a, **kw: func(*a, **kw)
            return func
        return decorator if not args else decorator(args[0])


@shared_task
def scrape_product_price(product_id):
    try:
        product = Product.objects.get(id=product_id)
        print(f"[TASK] Scraping: {product.name}")

        price = scrape_price(product.url)

        if not price:
            return {'status': 'error', 'message': 'Preço não encontrado'}

        product.last_price = price
        product.last_checked = timezone.now()
        product.save()

        PriceHistory.objects.create(product=product, price=price)

        return {'status': 'success', 'price': str(price)}

    except Product.DoesNotExist:
        return {'status': 'error', 'message': 'Produto não existe'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def scrape_all_products():
    products = Product.objects.all()
    for product in products:
        scrape_product_price.delay(product.id)
    return {'scheduled': products.count()}
