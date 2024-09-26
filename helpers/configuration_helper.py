from .json_helper import load_config_from_json
def load_configuration():
    """
    Yapılandırma dosyasını yükler ve gerekli değerleri döndürür.
    """
    config = load_config_from_json('config.json')
    return (
        config['spreadsheet_name'],
        config.get('interval_seconds', 240),
        config['camo_url'],
        config['writer_emails']
    )