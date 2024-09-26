from datetime import datetime

def get_date_components(tarih_str: str) -> str:
    """
    Verilen tarih stringini işleyerek 'YYYY-AA-GG' formatında bir string döndürür.

    Args:
        tarih_str (str): "%Y-%m-%d %H:%M:%S" formatında bir tarih stringi.

    Returns:
        str: 'YYYY-AA-GG' formatında tarih stringi.

    Raises:
        ValueError: Eğer verilen tarih stringi geçerli formatta değilse.
    """
    try:
        tarih = datetime.strptime(tarih_str, "%Y-%m-%d %H:%M:%S")
        return tarih.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Geçersiz tarih formatı. Lütfen 'YYYY-AA-GG SS:DD:SS' formatında bir tarih girin.")