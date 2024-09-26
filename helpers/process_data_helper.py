import pandas as pd
import typing

if typing.TYPE_CHECKING:
    from gspread import Spreadsheet

def read_and_preprocess_data(sheet: 'Spreadsheet') -> pd.DataFrame:
    """
    Google Sheets'ten veri okur, işler ve bir pandas DataFrame'e dönüştürür.

    Args:
        sheet (Spreadsheet): İşlenecek Google Sheets sayfası.

    Returns:
        pd.DataFrame: İşlenmiş veriyi içeren DataFrame.

    Raises:
        ValueError: Eğer sheet boş veya veri içermiyorsa.
    """
    # Sheet'den veriyi oku
    data = sheet.get_all_values()
    
    if not data:
        raise ValueError("Sheet boş veya veri içermiyor.")
    
    # İlk satır sütun isimleri değilse, sütun isimlerini ekle
    if data[0] != ['timestamp', 'number']:
        data.insert(0, ['timestamp', 'number'])
    
    # DataFrame oluştur
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # 'number' sütununun sayısal olduğundan emin ol
    df['number'] = pd.to_numeric(df['number'], errors='coerce')
    
    # Zaman damgasını datetime formatına çevir
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Geçersiz tarih veya sayı değerlerini içeren satırları at
    df = df.dropna(subset=['timestamp', 'number'])
    
    # Verileri zaman damgasına göre sırala
    df = df.sort_values('timestamp')
    return df

def calculate_daily_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Günlük tıklanma sayısını timestamp sütunundan hesaplar.
    Bir önceki günün son değerini kullanır (eğer varsa), yoksa aynı günün ilk değerini kullanır.

    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.

    Returns:
        pd.DataFrame: Günlük tıklanma sayılarını içeren DataFrame.
    """
    # 'timestamp' sütunundan tarih bilgisini çıkar ve günlük gruplandırma yap
    daily_clicks_df = df.groupby(df['timestamp'].dt.date)['number'].agg(['first', 'last'])
    
    # Bir önceki günün son değerini hesapla
    daily_clicks_df['prev_day_last'] = daily_clicks_df['last'].shift(1)
    
    # Günlük tıklanma sayısını hesapla
    daily_clicks_df['daily_clicks'] = daily_clicks_df.apply(
        lambda row: row['last'] - (row['prev_day_last'] if pd.notnull(row['prev_day_last']) else row['first']),
        axis=1
    )
    
    return daily_clicks_df[['daily_clicks']]




def calculate_average_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """
    2 saatlik ortalama tıklanma sayısını hesaplar.

    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.

    Returns:
        pd.DataFrame: Her gün için 2 saatlik ortalama tıklanma sayılarını içeren DataFrame.
    """
    # 2 saatlik ortalama tıklanma sayısını hesapla
    average_clicks_list = []
    
    for date in df['date'].unique():
        # Belirli bir günün verilerini al
        day_data = df[df['date'] == date].copy()
        day_data.set_index('timestamp', inplace=True)
        
        # 'number' sütunundaki farkları hesapla
        day_data['number_diff'] = day_data['number'].diff()
        day_data['number_diff'] = day_data['number_diff'].clip(lower=0)  # Negatif farkları sıfırla
        
        # 2 saatlik aralıklarla verileri yeniden örnekle ve tıklanma sayılarını topla
        resampled = day_data['number_diff'].resample('2h').sum()
        
        # 2 saatlik periyotların ortalamasını al
        if not resampled.empty:
            average_clicks = resampled.mean()
        else:
            average_clicks = 0  # Veri yoksa ortalama tıklanma sayısını 0 olarak al
        
        average_clicks_list.append({'date': date, 'average_clicks': average_clicks})
    
    # Sonuçları DataFrame şeklinde düzenle
    average_clicks_df = pd.DataFrame(average_clicks_list)
    average_clicks_df.set_index('date', inplace=True)
    
    return average_clicks_df
