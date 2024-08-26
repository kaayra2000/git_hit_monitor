import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from constants import CREDENTIAL_FILE
from datetime import datetime
from typing import Union
# API'ler için kapsamları tanımlayın
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDENTIAL_FILE, scopes=scopes)
client = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

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
def append_to_sheet(sheet: gspread.Worksheet, input_value: Union[str, int, float]) -> bool:
    """
    Verilen değeri (string, int veya float) ve anlık tarihi, sheet dosyasının yazılmayan son satırına ekler
    ve işlemin başarılı olup olmadığını döndürür.

    Args:
        sheet (gspread.Worksheet): İşlem yapılacak Google Sheet nesnesi.
        input_value (Union[str, int, float]): Sheet'e eklenecek değer.

    Returns:
        bool: İşlemin başarılı olup olmadığını belirten değer.
    """
    try:
        # Anlık tarihi al
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Yeni satır verilerini hazırla
        new_row = [current_date, input_value]
        
        # Sheet'e yeni satırı ekle
        sheet.append_row(new_row)
        
        # İşlem başarılıysa True döndür
        return True
    except Exception as e:
        # İşlem başarısızsa False döndür
        return False

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
