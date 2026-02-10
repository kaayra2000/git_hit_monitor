import sys
import time
import select
import tty
import termios
from typing import Optional, Callable

def countdown_timer(interval_seconds: int, on_keypress: Optional[Callable[[], None]] = None) -> None:
    """
    Belirtilen süre boyunca geri sayım yapan zamanlayıcı.
    
    Opsiyonel olarak tuş girişi dinler ve tuşa basıldığında
    verilen callback fonksiyonunu çağırır.

    Args:
        interval_seconds: Geri sayım için saniye cinsinden süre.
        on_keypress: Tuşa basıldığında çağrılacak callback fonksiyonu.
    """
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while interval_seconds > 0:
            info = get_info_str(interval_seconds)
            if on_keypress:
                info += " (Görsel için bir tuşa basın)"
            
            sys.stdout.write(info)
            sys.stdout.flush()
            
            # 1 saniye bekle, bu süre içinde tuş girişi kontrol et
            ready, _, _ = select.select([sys.stdin], [], [], 1.0)
            if ready and on_keypress:
                sys.stdin.read(1)  # tuşu oku ve temizle
                sys.stdout.write('\r' + ' ' * len(info) + '\r')
                on_keypress()
            
            sys.stdout.write('\r' + ' ' * len(info) + '\r')
            interval_seconds -= 1
        
        sys.stdout.write('\033[1A')  # Bir satır yukarı çık
        sys.stdout.flush()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

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
