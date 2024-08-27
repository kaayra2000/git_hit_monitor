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
    for i in range(interval_seconds, 0, -1):
        info = f"\r{i} saniye kaldı"
        sys.stdout.write(info)
        sys.stdout.flush()
        time.sleep(1)
    
    sys.stdout.write('\r' + ' ' * len(info) + '\r')  # Satırı boşluklarla doldur ve başa dön
    sys.stdout.write('\033[1A')  # Bir satır yukarı çık
    sys.stdout.flush()