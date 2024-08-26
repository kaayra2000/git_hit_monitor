import json

def load_config_from_json(file_path: str) -> dict:
    """
    Belirtilen JSON dosyasını okuyarak yapılandırma bilgilerini döndürür.

    Args:
        file_path (str): JSON dosyasının yolu.

    Returns:
        dict: Yapılandırma bilgilerini içeren sözlük.
    """
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config