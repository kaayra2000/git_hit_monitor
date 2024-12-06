import pandas as pd
import typing
import numpy as np
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
    
    if not data or data[0] == []:
        return pd.DataFrame(columns=['timestamp', 'number'])
    
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
    return calculate_clicks(df, period_days=1, column_name='daily_clicks')

def generate_clicks_dataframe(base_df: pd.DataFrame) -> pd.DataFrame:
    """
    base_df'yi alır ve toplam tıklanma sayısını içeren veriyi, periyotlar arası tıklanma sayısına dönüştürür.
    Bu işlemi yaparken veriyi işler ve bir pandas DataFrame döndürür.

    Args:
        base_df (pd.DataFrame): İşlenecek DataFrame.

    Returns:
        pd.DataFrame: İşlenmiş veriyi içeren DataFrame.
    
    Raises:
        ValueError: Eğer sheet boş veya veri içermiyorsa.
    """

    # Veriyi pandas DataFrame'e dönüştürüyoruz
    df = base_df.copy()
    
    # 'number' sütunundaki artışları hesaplıyoruz
    df['count'] = df['number'].diff().fillna(1)
    
    # İstenen sütunları seçiyoruz
    clicks_dataframe = df[['timestamp', 'count']]
    
    return clicks_dataframe

def convert_and_sort_timestamps(clicks_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Zaman damgalarını pd.Timestamp formatına dönüştürür ve sıralar.

    Args:
        clicks_dataframe (pd.DataFrame): İşlenecek DataFrame.
    
    Returns:
        pd.DataFrame: Zaman damgaları düzenlenmiş ve zaman damgası sırasına göre sıralanmış DataFrame.
    """
    clicks_dataframe['timestamp'] = pd.to_datetime(clicks_dataframe['timestamp']) # Zaman damgalarını datetime formatına dönüştür
    clicks_dataframe = clicks_dataframe.sort_values('timestamp') # Zaman damgalarına göre sırala
    return clicks_dataframe

def generate_and_prepare_clicks_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    clicks_dataframe'i oluşturur, zaman damgalarını pd.Timestamp formatına dönüştürür ve zaman damgalarına göre sıralar.
    
    Args:
        df (pd.DataFrame): İşlenecek DataFrame
    
    Returns:
        pd.DataFrame: Hazırlanmış DataFrame
    """
    clicks_dataframe = generate_clicks_dataframe(df)
    return convert_and_sort_timestamps(clicks_dataframe)

def calculate_interval_durations(clicks_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    clicks_dataframe'deki tıklama aralıklarını hesaplar. Bunu yapmasının sebebi tıklama sayılarını belli periyodlarla (günlük/aylık/yıllık vb.)
    hesaplayabilmektir.
    
    Args:
        clicks_dataframe (pd.DataFrame): İşlenecek DataFrame
    
    Returns:
        pd.DataFrame: Aralık süreleri eklenmiş DataFrame
    """
    clicks_dataframe['prev_timestamp'] = clicks_dataframe['timestamp'].shift(1) # Bir önceki elemanın zaman damgasını al
    # İlk elemanın önceki zaman damgasını kendisiyle eşitle (çünkü yok)
    clicks_dataframe.loc[clicks_dataframe.index[0], 'prev_timestamp'] = clicks_dataframe.loc[clicks_dataframe.index[0], 'timestamp']
    # Aralıklar arasında geçen süreyi sanise cinsinden hesapla
    clicks_dataframe['interval_duration'] = (clicks_dataframe['timestamp'] - clicks_dataframe['prev_timestamp']).dt.total_seconds()
    # 0 olan süreleri çok küçük bir değerle değiştir (sıfıra bölme hatasını önlemek için)
    clicks_dataframe['interval_duration'] = clicks_dataframe['interval_duration'].replace(0, np.finfo(float).eps)
    return clicks_dataframe

def process_single_period(count: float, period_start: pd.Timestamp) -> dict:
    """
    Bir periyod sadece tek elemandan oluşuyorsa tıklama sayısı ve başlangıç zamanınını içeren sözlük oluşturur.
    
    Args:
        count (float): Tıklama sayısı
        period_start (pd.Timestamp): Periyot başlangıç zamanı
        
    Returns:
        dict: Periyot başlangıcı ve tıklama sayısını içeren sözlük
    """
    return {
        'period_start': period_start,    # Sözlüğe periyot başlangıç zamanını ekler
        'clicks_per_period': count       # Sözlüğe tıklama sayısını ekler
    }

def process_multiple_periods(row: pd.Series, period_starts: pd.DatetimeIndex, 
                             column_name: str) -> list:
    """
    Birden fazla periyot için tıklama sayılarını hesaplar ve periyotlara dağıtır.
    
    Args:
        row (pd.Series): İşlenecek veri satırı
        period_starts (pd.DatetimeIndex): Periyot başlangıç zamanlarının listesi
        column_name (str): Sonuç sözlüğünde kullanılacak sütun adı
        
    Returns:
        list: Her periyot için tıklama sayılarını içeren sözlüklerden oluşan bir liste
    """
    period_counts = []  # Her periyot için tıklama sayılarını saklamak için boş bir liste oluştur

    # Her periyot için işlemleri tekrarla
    for i in range(len(period_starts) - 1):
        period_start = period_starts[i]       # Şu anki periyot başlangıç zamanı
        period_end = period_starts[i+1]       # Bir sonraki periyot başlangıç zamanı (şu anki periyot için bitiş zamanı)
        
        # Tıklama aralığı ile periyot arasındaki örtüşmenin başlangıç ve bitiş zamanlarını bul
        overlap_start = max(row['prev_timestamp'], period_start)  # Örtüşmenin başladığı zaman
        overlap_end = min(row['timestamp'], period_end)           # Örtüşmenin bittiği zaman
        overlap_duration = (overlap_end - overlap_start).total_seconds()  # Örtüşme süresini saniye cinsinden hesapla
        
        # Örtüşme süresinin toplam tıklama aralığı süresine oranını bul
        proportion = overlap_duration / row['interval_duration']  # Örtüşme oranı
        allocated_count = row['count'] * proportion               # Tıklama sayısını bu orana göre dağıt
        
        # Her periyot için başlangıç zamanı ve hesaplanan tıklama sayısını sözlük olarak listeye ekle
        period_counts.append({
            'period_start': period_start,     # Periyot başlangıç zamanı
            column_name: allocated_count      # Hesaplanan tıklama sayısı
        })

    return period_counts  # Her periyot için tıklama sayılarını içeren listeyi döndür

def calculate_clicks(df: pd.DataFrame, period_days: int = 1, 
                     column_name: str = 'clicks_per_period') -> pd.DataFrame:
    """
    Ana fonksiyon: Periyodik tıklama sayılarını hesaplar.
    
    Args:
        df (pd.DataFrame): İşlenecek DataFrame
        period_days (int): Gün periyodu (varsayılan 1)
        column_name (str): Sonuç sütun adı (varsayılan 'clicks_per_period')
    
    Returns:
        pd.DataFrame: Periyodik tıklama sayıları
    """
    period_type = 'D' # Periyot tipi (günlük)
    # Tıklama verilerini hazırlar ve zaman damgalarını düzenler
    df = generate_and_prepare_clicks_dataframe(df)
    
    # Tıklama aralıklarının sürelerini hesaplar
    df = calculate_interval_durations(df)
    
    # Her periyot için tıklama sayılarını saklamak üzere boş bir liste oluşturur
    period_counts = []
    
    # DataFrame'deki her satır için işlem yapar
    for _, row in df.iterrows():
        # Periyot frekansını belirler (örneğin '1D' günlük periyot için)
        period_freq = f'{period_days}{period_type}'
        
        # Periyot başlangıçlarını belirler
        period_starts = pd.date_range(
            start=row['prev_timestamp'].floor(period_type),  # Önceki zaman damgasını aşağı yuvarlar (günün başlangıcı)
            end=row['timestamp'].floor(period_type) + pd.Timedelta(days=period_days),  # Mevcut zaman damgasını aşağı yuvarlar ve periyot gününü ekler
            freq=period_freq  # Belirlenen periyot frekansı
        )
        
        # Eğer tıklama aralığı tek bir periyota denk geliyorsa
        if len(period_starts) == 1:
            # Tek periyot için tıklama sayısını hesaplar ve listeye ekler
            period_counts.append(process_single_period(
                row['count'], period_starts[0]
            ))
        else:
            # Tıklama aralığı birden fazla periyotu kapsıyorsa
            # Tıklama sayısını periyotlara dağıtarak hesaplar ve listeye ekler
            period_counts.extend(process_multiple_periods(row, period_starts, column_name))
    
    #Tüm periyotları ve tıklama sayılarını içeren bir DataFrame oluşturur
    result_df = pd.DataFrame(period_counts)
    
    # Periyot başlangıçlarına göre tıklama sayılarını toplar ve yuvarlar
    result_df = result_df.groupby('period_start')[column_name].sum().round(2)
    
    # Sonucu bir DataFrame olarak döndürür
    return result_df.to_frame()



def calculate_monthly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aylık tıklanma sayısını timestamp sütunundan hesaplar.

    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.

    Returns:
        pd.DataFrame: Aylık tıklanma sayılarını içeren DataFrame.
    """
    # 'timestamp' sütunundan ay bilgisini çıkar ve aylık gruplandırma yap
    monthly_clicks_df = df.groupby(df['timestamp'].dt.to_period('M'))['number'].agg(['first', 'last'])
    
    # Bir önceki ayın son değerini hesapla
    monthly_clicks_df['prev_month_last'] = monthly_clicks_df['last'].shift(1)
    
    # Aylık tıklanma sayısını hesapla
    monthly_clicks_df['monthly_clicks'] = monthly_clicks_df.apply(
        lambda row: row['last'] - (row['prev_month_last'] if pd.notnull(row['prev_month_last']) else row['first']),
        axis=1
    )
    # İndeksi datetime formatına dönüştür
    monthly_clicks_df.index = monthly_clicks_df.index.to_timestamp()
    
    return monthly_clicks_df[['monthly_clicks']]

def calculate_quarterly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """
    3 aylık tıklanma sayısını timestamp sütunundan hesaplar.

    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.

    Returns:
        pd.DataFrame: 3 aylık tıklanma sayılarını içeren DataFrame.
    """
    # 'timestamp' sütunundan çeyrek bilgisini çıkar ve çeyreklik gruplandırma yap
    quarterly_clicks_df = df.groupby(df['timestamp'].dt.to_period('Q'))['number'].agg(['first', 'last'])
    
    # Bir önceki çeyreğin son değerini hesapla
    quarterly_clicks_df['prev_quarter_last'] = quarterly_clicks_df['last'].shift(1)
    
    # Çeyreklik tıklanma sayısını hesapla
    quarterly_clicks_df['quarterly_clicks'] = quarterly_clicks_df.apply(
        lambda row: row['last'] - (row['prev_quarter_last'] if pd.notnull(row['prev_quarter_last']) else row['first']),
        axis=1
    )
    # İndeksi datetime formatına dönüştür
    quarterly_clicks_df.index = quarterly_clicks_df.index.to_timestamp()
    return quarterly_clicks_df[['quarterly_clicks']]
def calculate_yearly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Yıllık tıklanma sayısını timestamp sütunundan hesaplar.

    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.

    Returns:
        pd.DataFrame: Yıllık tıklanma sayılarını içeren DataFrame.
    """
    # 'timestamp' sütunundan yıl bilgisini çıkar ve yıllık gruplandırma yap
    # df'yi değiştirmek yerine, gruplandırma için geçici bir yıl serisi oluşturuyoruz
    year_series = df['timestamp'].dt.year
    yearly_clicks_df = df.groupby(year_series)['number'].agg(['first', 'last'])

    # Bir önceki yılın son değerini hesapla
    yearly_clicks_df['prev_year_last'] = yearly_clicks_df['last'].shift(1)

    # Yıllık tıklanma sayısını hesapla
    def calculate_yearly_clicks_row(row):
        if pd.notnull(row['prev_year_last']):
            return row['last'] - row['prev_year_last']
        else:
            return row['last'] - row['first']

    yearly_clicks_df['yearly_clicks'] = yearly_clicks_df.apply(
        calculate_yearly_clicks_row,
        axis=1
    )

    # İndeksi datetime formatına dönüştür
    yearly_clicks_df.index = pd.to_datetime(yearly_clicks_df.index.astype(str), format='%Y')

    return yearly_clicks_df[['yearly_clicks']]



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
