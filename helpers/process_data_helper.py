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
    Zaman damgası sütunundan günlük tıklanma sayısını hesaplar.
    - Her gün için, günün son tık sayısından ilk tık sayısını çıkararak günlük tıklanma sayısını hesaplar.
    - Eğer bir güne ait kayıt yoksa, o günün tıklanma sayısını önceki ve sonraki kayıtlar arasındaki ortalama değerle tahmin eder.
    
    Args:
        df (pd.DataFrame): İşlenmiş veriyi içeren DataFrame.
    
    Returns:
        pd.DataFrame: Günlük tıklanma sayılarını içeren DataFrame.
    """
    df = df.copy()
    
    # Zaman damgası sütununu datetime formatına çevir
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Tarih bilgisini ayrı bir sütuna al
    df['date'] = df['timestamp'].dt.normalize()
    
    # Her gün için ilk ve son tık sayılarını al
    daily_clicks = get_daily_first_last(df)
    
    # Günlük tıklanma sayısını hesapla
    daily_clicks['daily_clicks'] = calculate_daily_clicks_difference(daily_clicks)
    
    # Tüm tarih aralığını kapsayacak şekilde yeniden indeksleme yap
    all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
    daily_clicks = daily_clicks.reindex(all_dates)
    daily_clicks.index.name = 'date'
    
    # Eksik günlerin tıklanma sayılarını tahmin et
    daily_clicks['daily_clicks'] = fill_missing_clicks(daily_clicks)
    
    # Sonucu hazırlayıp döndür
    result_df = daily_clicks[['daily_clicks']]
    
    return result_df

def get_daily_first_last(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her gün için ilk ve son tık sayılarını döndürür.
    
    Args:
        df (pd.DataFrame): Veri DataFrame'i.
    
    Returns:
        pd.DataFrame: Her gün için ilk ve son tık sayılarını içeren DataFrame.
    """
    # Her gün için ilk ve son tık sayılarını al
    daily_stats = df.groupby('date')['number'].agg(first='first', last='last')
    return daily_stats

def calculate_daily_clicks_difference(daily_clicks: pd.DataFrame) -> pd.Series:
    """
    Günlük tıklanma sayılarını hesaplar.
    
    Args:
        daily_clicks (pd.DataFrame): Günlük ilk ve son tık sayılarını içeren DataFrame.
    
    Returns:
        pd.Series: Günlük tıklanma sayılarını içeren seri.
    """
    # Günlük tıklanma sayısını hesapla
    return daily_clicks['last'] - daily_clicks['first']

def fill_missing_clicks(daily_clicks: pd.DataFrame) -> pd.Series:
    """
    Eksik günlerin tıklanma sayılarını tahmin eder.
    
    Args:
        daily_clicks (pd.DataFrame): Günlük tıklanma sayılarını içeren DataFrame.
    
    Returns:
        pd.Series: Tahmin edilmiş günlük tıklanma sayılarını içeren seri.
    """
    clicks = daily_clicks['daily_clicks']
    is_missing = clicks.isna()
    
    # Eksik günlerin tarihlerini al
    missing_dates = clicks[is_missing].index
    
    # Eksik günler için tıklanma sayılarını tahmin et
    for missing_date in missing_dates:
        # Önceki ve sonraki veri olan tarihleri bul
        prev_date = find_prev_date_with_data(daily_clicks, missing_date)
        next_date = find_next_date_with_data(daily_clicks, missing_date)
        
        if prev_date and next_date:
            # Toplam gün sayısı (eksik günler dahil)
            total_days = (next_date - prev_date).days
            # Toplam tıklanma sayısı farkı
            total_clicks = daily_clicks.at[next_date, 'first'] - daily_clicks.at[prev_date, 'last']
            # Günlük ortalama tıklanma sayısı
            avg_clicks = total_clicks / total_days
            # Eksik günün tıklanma sayısını belirle
            clicks.at[missing_date] = avg_clicks
        else:
            # Önceki veya sonraki tarih yoksa tıklanma sayısını 0 olarak kabul et
            clicks.at[missing_date] = 0
    
    return clicks

def find_prev_date_with_data(daily_clicks: pd.DataFrame, current_date: pd.Timestamp) -> pd.Timestamp or None:
    """
    Mevcut tarihten önceki veri içeren en yakın tarihi bulur.
    
    Args:
        daily_clicks (pd.DataFrame): Günlük tıklanma sayılarını içeren DataFrame.
        current_date (pd.Timestamp): Mevcut tarih.
    
    Returns:
        pd.Timestamp veya None: Önceki veri içeren tarih veya None.
    """
    # Mevcut tarihten önceki tarihleri al
    prev_dates = daily_clicks.loc[:current_date].iloc[:-1]
    # Veri olan tarihleri filtrele
    prev_dates = prev_dates[prev_dates['last'].notna()]
    if not prev_dates.empty:
        return prev_dates.index[-1]
    else:
        return None

def find_next_date_with_data(daily_clicks: pd.DataFrame, current_date: pd.Timestamp) -> pd.Timestamp or None:
    """
    Mevcut tarihten sonraki veri içeren en yakın tarihi bulur.
    
    Args:
        daily_clicks (pd.DataFrame): Günlük tıklanma sayılarını içeren DataFrame.
        current_date (pd.Timestamp): Mevcut tarih.
    
    Returns:
        pd.Timestamp veya None: Sonraki veri içeren tarih veya None.
    """
    # Mevcut tarihten sonraki tarihleri al
    next_dates = daily_clicks.loc[current_date:].iloc[1:]
    # Veri olan tarihleri filtrele
    next_dates = next_dates[next_dates['first'].notna()]
    if not next_dates.empty:
        return next_dates.index[0]
    else:
        return None
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
