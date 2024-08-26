import requests
from bs4 import BeautifulSoup
import re

def get_number_from_url(url: str) -> str:
    """
    Verilen URL'ye istek atar ve içeriğindeki tüm SVG text elemanlarından sayıyı döndürür.

    Args:
        url (str): İşlem yapılacak URL.

    Returns:
        str: İlk bulunan SVG text elemanındaki sayı.
    """
    try:
        # URL'ye istek at
        response = requests.get(url)
        response.raise_for_status()  # İstek başarısız olursa hata fırlatır

        # HTML içeriğini işle
        soup = BeautifulSoup(response.content, 'html.parser')

        # Tüm text elemanlarını bul
        text_elements = soup.find_all('text')

        # Her bir text elemanını kontrol et
        for text_element in text_elements:
            if text_element and text_element.text:
                # Sayısal bir değer içerip içermediğini kontrol et
                match = re.search(r'[\d,.Kk]+', text_element.text)
                if match:
                    return match.group().strip()

        return "Belirtilen SVG text elemanı bulunamadı."

    except requests.exceptions.RequestException as e:
        return f"HTTP isteği başarısız: {e}"