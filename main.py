from helpers import sheets_helper, camo_helper, string_helper, json_helper, timer_helper
import time
import sys
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
    
    # Google Sheet URL'sini oluştur
    sheet_url = f"https://docs.google.com/spreadsheets/d/{file_id}"
    print(f"Google Sheet URL: {sheet_url}")
    
    # Erişim izinlerini ayarla
    sheets_helper.apply_permission(file_id, sheets_helper.create_public_access_permission())
    sheets_helper.share_sheet_with_emails(spreadsheet, writer_emails)
    append_counter = 0
    try:
        while True:
            view_count_str, is_successful = camo_helper.get_number_from_url(camo_url)
            if not is_successful:
                print(f"\n{view_count_str}")
                break
            view_count = string_helper.convert_to_int(view_count_str)
            if sheets_helper.append_to_sheet(sheet, view_count):
                append_counter += 1
                # Çıktıyı aynı satıra yazdır
                sys.stdout.write(f"\r{append_counter}. ekleme yapıldı. Şu anki görüntülenme sayısı: {view_count}\n")
                sys.stdout.flush()
                
                timer_helper.countdown_timer(interval_seconds)
            else:
                print("\nGörüntülenme sayısı eklenirken bir hata oluştu.")
                break
    except KeyboardInterrupt:
        print("\nZamanlayıcı durduruldu.")



# Ana fonksiyonu çalıştır
if __name__ == "__main__":
    main()
