def convert_to_int(number_str: str) -> int:
    """
    Bir string sayıyı alır, harfleri ve diğer karakterleri kaldırarak tam sayı olarak döndürür.
    Eğer 'K' harfi varsa, sayıyı 1000 ile çarpar.

    Args:
        number_str (str): İşlem yapılacak string sayı.

    Returns:
        int: Harflerden ve diğer karakterlerden arındırılmış tam sayı.
    """
    # 'K' harfi varsa, sayıyı 1000 ile çarp
    if 'K' in number_str.upper():
        # 'K' harfini kaldır
        number_str = number_str.upper().replace('K', '')
        multiplier = 1000
    else:
        multiplier = 1

    # Virgülü nokta ile değiştirip float'a dönüştür
    number_str = number_str.replace(',', '')
    
    # String'i float'a dönüştür ve çarpan ile çarp
    number = float(number_str) * multiplier
    
    # Sonuç olarak tam sayı döndür
    return int(number)


if __name__ == "__main__":
    print(convert_to_int("39.7K"))  # Çıktı: 39700
    print(convert_to_int("39,689"))  # Çıktı: 39689