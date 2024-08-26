import requests
from bs4 import BeautifulSoup

def get_number_from_url(url: str) -> str:
    """
    Verilen URL'ye istek atar ve içeriğindeki belirli bir SVG text elemanından sayıyı döndürür.

    Args:
        url (str): İşlem yapılacak URL.

    Returns:
        str: SVG text elemanındaki sayı.
    """
    try:
        # URL'ye istek at
        response = requests.get(url)
        response.raise_for_status()  # İstek başarısız olursa hata fırlatır

        # HTML içeriğini işle
        soup = BeautifulSoup(response.content, 'html.parser')

        # Belirli SVG text elemanını bul
        text_element = soup.find('text', {'x': '102.5', 'y': '15', 'fill': '#010101', 'fill-opacity': '.3'})
        
        if text_element:
            return text_element.text.strip()
        else:
            return "Belirtilen SVG text elemanı bulunamadı."

    except requests.exceptions.RequestException as e:
        return f"HTTP isteği başarısız: {e}"