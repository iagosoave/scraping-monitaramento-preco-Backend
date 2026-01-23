# PriceWatch - Backend

API para monitoramento de preços.

## Tecnologias

- Django 5
- Django REST Framework
- BeautifulSoup (scraping)

## Sites compatíveis

- Kabum
- Trocafone

## Rodar local

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Endpoints

- `GET /api/products/` - lista produtos
- `POST /api/products/` - cria produto
- `DELETE /api/products/{id}/` - remove produto
- `POST /api/products/{id}/scrape/` - atualiza preço
- `GET /api/products/{id}/history/` - histórico de preços

## Deploy no Railway

1. Conecte o repositório no Railway
2. Configure as variáveis: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
