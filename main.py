from helpers import sheets_helper, camo_helper, string_helper, json_helper
import time
def main():
    # JSON dosyasını yükle
    config = json_helper.load_config_from_json('config.json')
    # JSON'dan değerleri al
    spreadsheet_name = config['spreadsheet_name']
    interval_seconds = config['interval_seconds']
    camo_url = config['camo_url']
    writer_emails = config['writer_emails']
    mime_type = 'application/vnd.google-apps.spreadsheet'
    spreadsheet = sheets_helper.get_spreadsheet(spreadsheet_name, mime_type)
    sheet = spreadsheet.sheet1
    file_id = spreadsheet.id
    # Erişim izinlerini ayarla
    sheets_helper.apply_permission(file_id, sheets_helper.create_public_access_permission())
    sheets_helper.share_sheet_with_emails(spreadsheet, writer_emails)
    try:
        while True:
            view_count_str = camo_helper.get_number_from_url(camo_url)
            view_count = string_helper.convert_to_int(view_count_str)
            sheets_helper.append_to_sheet(sheet, view_count)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("Zamanlayıcı durduruldu.")



# Ana fonksiyonu çalıştır
if __name__ == "__main__":
    main()
