import re
import json
import requests
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse


def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }


def fetch_page(url):
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[SCRAPER] Erro: {e}")
        return None


def clean_price(price_text):
    if not price_text:
        return None

    cleaned = re.sub(r'[^\d.,]', '', str(price_text))
    if not cleaned:
        return None

    if ',' in cleaned and '.' in cleaned:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def get_site_name(url):
    domain = urlparse(url).netloc.lower()
    if 'mercadolivre' in domain:
        return 'mercadolivre'
    elif 'kabum' in domain:
        return 'kabum'
    elif 'pichau' in domain:
        return 'pichau'
    elif 'terabyte' in domain:
        return 'terabyte'
    elif 'amazon' in domain:
        return 'amazon'
    elif 'magalu' in domain or 'magazineluiza' in domain:
        return 'magalu'
    elif 'americanas' in domain:
        return 'americanas'
    elif 'casasbahia' in domain:
        return 'casasbahia'
    elif 'extra.com' in domain:
        return 'extra'
    return 'generic'


def scrape_mercadolivre(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and 'offers' in item:
                        offers = item['offers']
                        price = offers.get('price') if isinstance(offers, dict) else offers[0].get('price') if offers else None
                        if price and float(price) > 50:
                            return Decimal(str(price))
        except:
            pass

    prices = re.findall(r'"price"\s*:\s*(\d{3,}\.?\d*)', html)
    for p in prices:
        price = clean_price(p)
        if price and price > 50:
            return price

    return None


def scrape_kabum(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    price = data['offers'].get('price')
                    if price:
                        return Decimal(str(price))
        except:
            pass

    for pattern in [r'"priceWithDiscount"\s*:\s*(\d+\.?\d*)', r'"price"\s*:\s*(\d+\.?\d*)']:
        match = re.search(pattern, html)
        if match:
            price = clean_price(match.group(1))
            if price and price > 10:
                return price

    return None


def scrape_magalu(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            data = item
                            break
                
                if isinstance(data, dict):
                    if 'offers' in data:
                        offers = data['offers']
                        if isinstance(offers, dict):
                            price = offers.get('price') or offers.get('lowPrice')
                            if price:
                                return Decimal(str(price))
                        elif isinstance(offers, list) and offers:
                            price = offers[0].get('price')
                            if price:
                                return Decimal(str(price))
        except:
            pass

    patterns = [
        r'"price"\s*:\s*"?(\d+\.?\d*)"?',
        r'"bestPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"lowPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"sellingPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'data-price="(\d+\.?\d*)"',
        r'"installmentPrice"\s*:\s*"?(\d+\.?\d*)"?',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            price = clean_price(match)
            if price and price > 50:
                return price

    price_match = re.search(r'R\$\s*([\d.,]+)', html)
    if price_match:
        price = clean_price(price_match.group(1))
        if price and price > 50:
            return price

    return None


def scrape_pichau(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    price = data['offers'].get('price')
                    if price:
                        return Decimal(str(price))
        except:
            pass

    return None


def scrape_terabyte(html):
    soup = BeautifulSoup(html, 'html.parser')

    el = soup.select_one('#valVista')
    if el:
        price = clean_price(el.get_text())
        if price and price > 10:
            return price

    return None


def scrape_amazon(html):
    soup = BeautifulSoup(html, 'html.parser')

    for selector in ['.a-price .a-offscreen', '#priceblock_ourprice', '#priceblock_dealprice']:
        el = soup.select_one(selector)
        if el:
            price = clean_price(el.get_text())
            if price and price > 10:
                return price

    return None


def scrape_americanas(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    offers = data['offers']
                    price = offers.get('price') or offers.get('lowPrice') if isinstance(offers, dict) else None
                    if price:
                        return Decimal(str(price))
        except:
            pass

    patterns = [r'"price"\s*:\s*(\d+\.?\d*)', r'"bestPrice"\s*:\s*(\d+\.?\d*)']
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            price = clean_price(match.group(1))
            if price and price > 10:
                return price

    return None


def scrape_generic(html):
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            if script.string:
                data = json.loads(script.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and 'offers' in item:
                        offers = item['offers']
                        price = offers.get('lowPrice') or offers.get('price') if isinstance(offers, dict) else None
                        if price:
                            return Decimal(str(price))
        except:
            pass

    for selector in ['meta[property="product:price:amount"]', 'meta[itemprop="price"]']:
        meta = soup.select_one(selector)
        if meta:
            price = clean_price(meta.get('content'))
            if price and price > 10:
                return price

    patterns = [
        r'"price"\s*:\s*"?(\d+\.?\d*)"?',
        r'"lowPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"bestPrice"\s*:\s*"?(\d+\.?\d*)"?',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            price = clean_price(match.group(1))
            if price and price > 10:
                return price

    return None


def scrape_price(url):
    print(f"[SCRAPER] Buscando: {url}")

    html = fetch_page(url)
    if not html:
        return None

    site = get_site_name(url)
    print(f"[SCRAPER] Site: {site}")

    scrapers = {
        'mercadolivre': scrape_mercadolivre,
        'kabum': scrape_kabum,
        'pichau': scrape_pichau,
        'terabyte': scrape_terabyte,
        'amazon': scrape_amazon,
        'magalu': scrape_magalu,
        'americanas': scrape_americanas,
        'casasbahia': scrape_americanas,
        'extra': scrape_americanas,
        'generic': scrape_generic,
    }

    price = scrapers.get(site, scrape_generic)(html)

    if not price and site != 'generic':
        price = scrape_generic(html)

    if price:
        print(f"[SCRAPER] Preço: R$ {price}")
    else:
        print("[SCRAPER] Preço não encontrado")

    return price