import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from constants import CREDENTIAL_FILE
from datetime import datetime
from typing import Union, Tuple, Any
# API'ler için kapsamları tanımlayın
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIAL_FILE, scopes=scopes)
client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)


def configure_sheet_permissions(file_id: str, spreadsheet: Any, writer_emails: list[str]) -> None:
    """
    Çalışma sayfasının izinlerini ayarlar.

    Bu fonksiyon, verilen Google Sheets çalışma sayfasının izinlerini yapılandırır.
    Önce çalışma sayfasını herkese açık hale getirir, ardından belirli e-posta 
    adreslerine yazma izni verir.

    Args:
        file_id (str): Çalışma sayfasının benzersiz dosya kimliği.
        spreadsheet (Any): Google Sheets çalışma sayfası nesnesi.
        writer_emails (list[str]): Yazma izni verilecek e-posta adreslerinin listesi.

    Returns:
        None

    Not:
        Bu fonksiyon, sheets_helper modülünden fonksiyonlar kullanmaktadır.
        Bu modülün tanımı ve içeriği bu kod parçasında görünmemektedir.
    """
    # Çalışma sayfasının URL'sini oluştur
    sheet_url = f"https://docs.google.com/spreadsheets/d/{file_id}"
    print(f"Google Sheet URL: {sheet_url}")  # URL'yi konsola yazdır
    
    # Çalışma sayfasını herkese açık hale getir
    apply_permission(file_id, create_public_access_permission())
    
    # Belirtilen e-posta adreslerine yazma izni ver
    share_sheet_with_emails(spreadsheet, writer_emails)


def setup_spreadsheet(spreadsheet_name: str) -> tuple[Any, Any, str]:
    """
    Google Sheets'te bir çalışma sayfası oluşturur ve gerekli bilgileri döndürür.

    Bu fonksiyon, verilen isimde bir Google Sheets çalışma sayfası oluşturur veya
    varsa mevcut olanı açar. Oluşturulan veya açılan çalışma sayfasının kendisini,
    ilk sayfasını ve dosya kimliğini döndürür.

    Args:
        spreadsheet_name (str): Oluşturulacak veya açılacak çalışma sayfasının adı.

    Returns:
        tuple[Any, Any, str]: 
            - spreadsheet (Any): Oluşturulan veya açılan Google Sheets çalışma sayfası nesnesi.
            - sheet (Any): Çalışma sayfasının ilk sayfası (sheet1).
            - file_id (str): Oluşturulan veya açılan çalışma sayfasının benzersiz dosya kimliği.

    Not:
        Bu fonksiyon, get_spreadsheet() adlı başka bir fonksiyonu kullanır. Bu fonksiyonun
        tanımı ve içeriği bu kod parçasında görünmemektedir.
    """
    mime_type = 'application/vnd.google-apps.spreadsheet'
    spreadsheet = get_spreadsheet(spreadsheet_name, mime_type)  # Google Sheets çalışma sayfası oluşturur veya açar
    sheet = spreadsheet.sheet1  # Çalışma sayfasının ilk sayfasını alır
    file_id = spreadsheet.id  # Çalışma sayfasının benzersiz kimliğini alır
    return spreadsheet, sheet, file_id  # Oluşturulan veya açılan çalışma sayfası, ilk sayfa ve dosya kimliğini döndürür



def create_sheets(spreadsheet_name: str, mime_type: str) -> gspread.Spreadsheet:
    """
    Yeni bir Google Sheet oluşturur ve döndürür.

    Args:
        spreadsheet_name (str): Oluşturulacak Google Sheet'in adı.
        mime_type (str): Dosyanın MIME türü, genellikle 'application/vnd.google-apps.spreadsheet'.

    Returns:
        gspread.Spreadsheet: Oluşturulan Google Sheet nesnesi.
    """
    file_metadata = {
        'name': spreadsheet_name,
        'mimeType': mime_type
    }
    spreadsheet = drive_service.files().create(body=file_metadata, fields='id').execute()
    return spreadsheet

def create_public_access_permission() -> dict:
    """
    Herkese açık erişim izni sözlüğünü döndürür.

    Returns:
        dict: Herkese açık okuma izni için gerekli olan izin sözlüğü.
    """
    return {
        'type': 'anyone',
        'role': 'reader'
    }

def apply_permission(file_id: str, permission: dict):
    """
    Verilen izin sözlüğünü kullanarak Google Sheet'e erişim izni verir.

    Args:
        file_id (str): Erişim izni verilecek dosyanın kimliği.
        permission (dict): Uygulanacak izin sözlüğü.
    """
    drive_service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()


def is_sheet_exists(spreadsheet_name: str, mime_type:str) -> tuple[bool, str | None]:
    """
    Belirtilen isimde bir Google Sheet'in var olup olmadığını kontrol eder.

    Args:
        spreadsheet_name (str): Kontrol edilecek Google Sheet'in adı.

    Returns:
        tuple: İlk eleman olarak bir boolean değer (True veya False),
               ikinci eleman olarak dosya kimliği (str) veya None.
               True ise dosya kimliği döner, False ise None döner.
    """
    file_list = drive_service.files().list(
        q=f"name='{spreadsheet_name}' and mimeType='{mime_type}'",
        fields="files(id, name)"
    ).execute()
    files = file_list.get('files', [])
    if files:
        return True, files[0]['id']
    return False, None


def get_spreadsheet(spreadsheet_name: str, mime_type: str) -> gspread.Spreadsheet:
    """
    Belirtilen isimdeki Google Sheet'i alır ve döndürür. Eğer yoksa yeni bir tane oluşturur.

    Args:
        spreadsheet_name (str): Alınacak veya oluşturulacak Google Sheet'in adı.
        mime_type (str): Dosyanın MIME türü, genellikle 'application/vnd.google-apps.spreadsheet'.

    Returns:
        gspread.Spreadsheet: Açılan veya oluşturulan Google Sheet nesnesi.
    """
    exists, file_id = is_sheet_exists(spreadsheet_name, mime_type)
    if exists:
        # Var olan dosyayı aç
        spreadsheet = client.open_by_key(file_id)
    else:
        # Dosya yoksa yeni bir dosya oluştur
        spreadsheet = create_sheets(spreadsheet_name, mime_type)
    return spreadsheet
def append_to_sheet(sheet: gspread.Worksheet, input_value: Union[str, int, float], value_threshold: Union[int, float] = 2) -> Tuple[bool, bool, datetime | str]:
    """
    Verilen değeri (string, int veya float) ve anlık tarihi, sheet dosyasının son satırına ekler veya günceller.
    Eğer son satırın 2. sütunu aynı değere sahipse, o satırı günceller; değilse yeni bir satır ekler.
    İşlemin başarılı olup olmadığını döndürür.

    Args:
        sheet (gspread.Worksheet): İşlem yapılacak Google Sheet nesnesi.
        input_value (Union[str, int, float]): Sheet'e eklenecek veya güncellenecek değer.
        value_threshold (Union[int, float]): İki değer arasındaki kabul edilebilir maksimum fark.
    Returns:
        bool: İşlemin başarılı olup olmadığını belirten değer.
        bool: Ekleme yapıldıysa True, güncelleme yapıldıysa False.
        datatime:  Ekleme yapılan zaman damgası.
    """
    is_appended = False
    try:
        # Anlık tarihi al ve formatla
        current_date = datetime.now()
        current_date_str = current_date.strftime("%Y-%m-%d %H:%M:%S")
        
        is_appended = update_sheet(sheet, sheet.get_all_values(), input_value, current_date_str, value_threshold)
        
        # İşlem başarılıysa True döndür
        return True, is_appended, current_date
    except Exception as e:
        # İşlem başarısızsa False döndür
        return False, is_appended, str(e)
def update_sheet(sheet: object, all_values: list, input_value: float, current_date_str: str, value_threshold: float) -> bool:
    """
    Bir Google Sheets sayfasını günceller veya yeni bir satır ekler.

    Args:
        sheet (object): Güncellenecek Google Sheets sayfası nesnesi.
        all_values (list): Sayfadaki mevcut tüm değerlerin listesi.
        input_value (float): Eklenecek veya karşılaştırılacak yeni değer.
        current_date_str (str): Mevcut tarih, string formatında.
        value_threshold (float): Kayan noktalı sayıları karşılaştırmak için eşik değeri.

    Returns:
        bool: Yeni bir satır eklendiyse True, aksi halde False.
    """

    def is_within_threshold(val1: float, val2: float) -> bool:
        """
        İki değerin belirli bir eşik içinde olup olmadığını kontrol eder.

        Args:
            val1 (float): Karşılaştırılacak ilk değer.
            val2 (float): Karşılaştırılacak ikinci değer.

        Returns:
            bool: Değerler eşik içindeyse True, değilse False.
        """
        try:
            return abs(float(val1) - float(val2)) <= value_threshold
        except ValueError:
            return False  # Değerler float'a dönüştürülemezse, eşik içinde olmadıklarını varsayıyoruz

    is_appended = False
    last_row = all_values[-1] if all_values else None
    second_last_row = all_values[-2] if len(all_values) > 1 else None

    if last_row and str(last_row[1]) == str(input_value):
        # Son satırın 2. sütunu aynı değere sahipse, son satırı güncelle
        row_number = len(all_values)
        sheet.update_cell(row_number, 1, f"'{current_date_str}")
    elif second_last_row and is_within_threshold(second_last_row[1], input_value):
        # Sondan bir önceki satır varsa ve değer farkı eşiğin altındaysa, son satırı güncelle
        row_number = len(all_values)
        sheet.update_cell(row_number, 1, f"'{current_date_str}")
        sheet.update_cell(row_number, 2, input_value)
    else:
        # Diğer durumlarda, yeni satır ekle
        new_row = [current_date_str, input_value]
        sheet.append_row(new_row)
        is_appended = True

    return is_appended



def share_sheet_with_emails(sheet: gspread.Spreadsheet, email_addresses: list[str]):
    """
    Verilen e-posta adreslerine sheet üzerinde "writer" yetkisi verir.
    Eğer e-posta adresine zaten "writer" yetkisi verilmişse tekrar vermeye çalışmaz.

    Args:
        sheet (gspread.Spreadsheet): İşlem yapılacak Google Sheet nesnesi.
        email_addresses (List[str]): Yetki verilecek e-posta adreslerinin listesi.
    """
    # Mevcut izinleri al
    permissions = sheet.list_permissions()
    
    for email in email_addresses:
        # E-posta adresine zaten "writer" yetkisi verilmiş mi kontrol et
        already_writer = any(p['emailAddress'] == email and p['role'] == 'writer' for p in permissions)
        
        if not already_writer:
            # Eğer yetki verilmemişse, yetki ver
            sheet.share(email, perm_type='user', role='writer')
            print(f"{email} adresine 'writer' yetkisi verildi.")
        else:
            print(f"{email} adresine zaten 'writer' yetkisi verilmiş.")
