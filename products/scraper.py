import re
import json
import requests
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
import time
import random


def get_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
    }


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            session = requests.Session()
            headers = get_headers()
            
            response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
            response.raise_for_status()
            
            if len(response.text) < 1000:
                print(f"[SCRAPER] Resposta muito curta, tentando novamente...")
                time.sleep(1)
                continue
                
            return response.text
        except requests.RequestException as e:
            print(f"[SCRAPER] Tentativa {attempt + 1} falhou: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
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
        price = Decimal(cleaned)
        if price > 0:
            return price
        return None
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
    return 'generic'


def extract_json_ld_price(html):
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', type='application/ld+json')
    
    for script in scripts:
        try:
            if not script.string:
                continue
                
            data = json.loads(script.string)
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                if item.get('@type') in ['Product', 'IndividualProduct', 'ProductModel']:
                    offers = item.get('offers', {})
                    
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    
                    if isinstance(offers, dict):
                        price = offers.get('price') or offers.get('lowPrice') or offers.get('highPrice')
                        if price:
                            try:
                                return Decimal(str(price))
                            except:
                                pass
                                
                if 'offers' in item:
                    offers = item['offers']
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict):
                        price = offers.get('price') or offers.get('lowPrice')
                        if price:
                            try:
                                return Decimal(str(price))
                            except:
                                pass
        except:
            pass
    
    return None


def extract_price_from_patterns(html, min_price=10):
    patterns = [
        r'"price"\s*:\s*(\d+\.?\d*)',
        r'"lowPrice"\s*:\s*(\d+\.?\d*)',
        r'"bestPrice"\s*:\s*(\d+\.?\d*)',
        r'"sellingPrice"\s*:\s*(\d+\.?\d*)',
        r'"priceWithDiscount"\s*:\s*(\d+\.?\d*)',
        r'"salePrice"\s*:\s*(\d+\.?\d*)',
        r'"finalPrice"\s*:\s*(\d+\.?\d*)',
        r'"spotPrice"\s*:\s*(\d+\.?\d*)',
        r'"priceValidUntil"[^}]*"price"\s*:\s*(\d+\.?\d*)',
        r'data-price="(\d+\.?\d*)"',
        r'content="(\d+\.?\d*)"[^>]*itemprop="price"',
        r'itemprop="price"[^>]*content="(\d+\.?\d*)"',
    ]
    
    all_prices = []
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            price = clean_price(match)
            if price and price > min_price:
                all_prices.append(price)
    
    if all_prices:
        price_count = {}
        for p in all_prices:
            p_str = str(p)
            price_count[p_str] = price_count.get(p_str, 0) + 1
        
        most_common = max(price_count, key=price_count.get)
        return Decimal(most_common)
    
    return None


def scrape_mercadolivre(html):
    price = extract_json_ld_price(html)
    if price and price > 50:
        return price
    
    price = extract_price_from_patterns(html, min_price=50)
    if price:
        return price
    
    return None


def scrape_kabum(html):
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    price = extract_price_from_patterns(html, min_price=10)
    if price:
        return price
    
    return None


def scrape_magalu(html):
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    patterns = [
        r'"price"\s*:\s*"?(\d+\.?\d*)"?',
        r'"bestPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"fullPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"installmentPrice"\s*:\s*"?(\d+\.?\d*)"?',
        r'"priceWithPaymentDiscount"\s*:\s*"?(\d+\.?\d*)"?',
        r'Por:</span>[^<]*R\$\s*([\d.,]+)',
        r'class="price[^"]*"[^>]*>R\$\s*([\d.,]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            price = clean_price(match)
            if price and price > 50:
                return price
    
    price = extract_price_from_patterns(html, min_price=50)
    if price:
        return price
    
    soup = BeautifulSoup(html, 'html.parser')
    
    meta = soup.find('meta', {'property': 'product:price:amount'})
    if meta and meta.get('content'):
        price = clean_price(meta['content'])
        if price and price > 10:
            return price
    
    meta = soup.find('meta', {'itemprop': 'price'})
    if meta and meta.get('content'):
        price = clean_price(meta['content'])
        if price and price > 10:
            return price
    
    return None


def scrape_pichau(html):
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    price = extract_price_from_patterns(html, min_price=10)
    if price:
        return price
    
    return None


def scrape_terabyte(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    el = soup.select_one('#valVista')
    if el:
        price = clean_price(el.get_text())
        if price and price > 10:
            return price
    
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    return None


def scrape_amazon(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    selectors = [
        '.a-price .a-offscreen',
        '#priceblock_ourprice',
        '#priceblock_dealprice', 
        '#corePrice_feature_div .a-offscreen',
        '.priceToPay .a-offscreen',
    ]
    
    for selector in selectors:
        el = soup.select_one(selector)
        if el:
            price = clean_price(el.get_text())
            if price and price > 10:
                return price
    
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    return None


def scrape_americanas(html):
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    price = extract_price_from_patterns(html, min_price=10)
    if price:
        return price
    
    return None


def scrape_generic(html):
    price = extract_json_ld_price(html)
    if price and price > 10:
        return price
    
    soup = BeautifulSoup(html, 'html.parser')
    
    meta_selectors = [
        ('meta', {'property': 'product:price:amount'}),
        ('meta', {'itemprop': 'price'}),
        ('meta', {'name': 'price'}),
    ]
    
    for tag, attrs in meta_selectors:
        meta = soup.find(tag, attrs)
        if meta and meta.get('content'):
            price = clean_price(meta['content'])
            if price and price > 10:
                return price
    
    price = extract_price_from_patterns(html, min_price=10)
    if price:
        return price
    
    return None


def scrape_price(url):
    print(f"[SCRAPER] Buscando: {url}")

    html = fetch_page(url)
    if not html:
        print("[SCRAPER] Falha ao buscar página")
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
        'generic': scrape_generic,
    }

    price = scrapers.get(site, scrape_generic)(html)

    if not price and site != 'generic':
        print("[SCRAPER] Tentando scraper genérico...")
        price = scrape_generic(html)

    if price:
        print(f"[SCRAPER] Preço: R$ {price}")
    else:
        print("[SCRAPER] Preço não encontrado")

    return price