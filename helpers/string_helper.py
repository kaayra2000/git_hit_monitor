def convert_to_int(number_str: str) -> int:
    """
    Virgüllü bir string sayıyı alır ve virgülü kaldırarak tam sayı olarak döndürür.

    Args:
        number_str (str): Virgüllü string sayı.

    Returns:
        int: Virgülsüz tam sayı.
    """
    # Virgülü kaldır
    number_str = number_str.replace(',', '')
    
    # String'i tam sayıya dönüştür
    return int(number_str)
