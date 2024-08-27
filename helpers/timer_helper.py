import sys
import time

def countdown_timer(interval_seconds: int) -> None:
    """
    Belirtilen süre boyunca geri sayım yapan ve sonunda satırı silen bir zamanlayıcı.

    Args:
        interval_seconds (int): Geri sayım için saniye cinsinden süre.

    Returns:
        None
    """
    while interval_seconds > 0:
        info = get_info_str(interval_seconds)
        
        sys.stdout.write(info)
        sys.stdout.flush()
        time.sleep(1)
        sys.stdout.write('\r' + ' ' * len(info) + '\r')  # Satırı boşluklarla doldur ve başa dön
        interval_seconds -= 1
    
    sys.stdout.write('\033[1A')  # Bir satır yukarı çık
    sys.stdout.flush()
def get_info_str(interval_seconds: int) -> str:
    """
    Verilen saniye cinsinden süreyi gün, ay, yıl, saat, dakika ve saniye cinsine çevirir
    ve uygun bir formatta geri döner.

    Args:
        interval_seconds (int): Geri sayım için saniye cinsinden süre.

    Returns:
        str: Zaman bilgilerini içeren formatlanmış bir string.
    """
    # Sabit değerler
    seconds_in_a_minute = 60  # Bir dakikadaki saniye sayısı
    minutes_in_an_hour = 60     # Bir saatteki dakika sayısı
    hours_in_a_day = 24         # Bir günde saat sayısı
    days_in_a_month = 30        # Ortalama bir ay için gün sayısı

    # Yıl, ay, gün, saat, dakika ve saniye hesaplama
    years, remainder = divmod(interval_seconds, 365 * hours_in_a_day * minutes_in_an_hour * seconds_in_a_minute)
    months, remainder = divmod(remainder, days_in_a_month * hours_in_a_day * minutes_in_an_hour * seconds_in_a_minute)
    days, remainder = divmod(remainder, hours_in_a_day * minutes_in_an_hour * seconds_in_a_minute)
    hours, remainder = divmod(remainder, minutes_in_an_hour * seconds_in_a_minute)
    minutes, seconds = divmod(remainder, seconds_in_a_minute)

    # Formatlama: Zaman birimlerine göre uygun string döndürme
    if years > 0:
        return f"\r{years} yıl, {months} ay, {days} gün, {hours:02}:{minutes:02}:{seconds:02} kaldı"
    elif months > 0:
        return f"\r{months} ay, {days} gün, {hours:02}:{minutes:02}:{seconds:02} kaldı"
    elif days > 0:
        return f"\r{days} gün, {hours:02}:{minutes:02}:{seconds:02} kaldı"
    elif hours > 0:
        return f"\r{hours}:{minutes:02}:{seconds:02} kaldı"
    elif minutes > 0:
        return f"\r{minutes}:{seconds:02} kaldı"
    else:
        return f"\r{seconds} saniye kaldı"
