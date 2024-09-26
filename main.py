from helpers import sheets_helper, process_view_count, timer_helper, process_data_helper, load_configuration
import sys
def main():
    # Yapılandırma dosyasını yükle
    spreadsheet_name, interval_seconds, camo_url, writer_emails = load_configuration()

    # Çalışma sayfasını ayarla
    spreadsheet, sheet, file_id = sheets_helper.setup_spreadsheet(spreadsheet_name)

    # Çalışma sayfası izinlerini yapılandır
    sheets_helper.configure_sheet_permissions(file_id, spreadsheet, writer_emails)

    # Veriyi oku ve ön işle
    df = process_data_helper.read_and_preprocess_data(sheet)

    append_counter = 0
    cycle_counter = 0
    try:
        while True:
            df, new_appends, view_count = process_view_count(camo_url, sheet, df)
            append_counter += new_appends
            cycle_counter += 1

            if view_count > 0:
                sys.stdout.write(f"\r{cycle_counter}. deneme ve {append_counter}. ekleme yapıldı. Şu anki görüntülenme sayısı: {view_count}\n")
                sys.stdout.flush()

            timer_helper.countdown_timer(interval_seconds)
    except KeyboardInterrupt:
        print("\nZamanlayıcı durduruldu.")



# Ana fonksiyonu çalıştır
if __name__ == "__main__":
    main()
