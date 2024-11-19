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
    Calculates the daily clicks based on the timestamp and number columns.
    
    - For each day, it takes the first and last records to compute the clicks difference.
    - If a day has no records, it fills the 'number_first' and 'number_last'
      by carrying forward the last valid values and backward filling from the next valid entries.
    - The daily clicks are scaled to a 24-hour period based on the time elapsed.
    
    Args:
        df (pd.DataFrame): The input DataFrame containing 'timestamp' and 'number' columns.
        
    Returns:
        pd.DataFrame: A DataFrame with 'daily_clicks' column indexed by 'date'.
    """
    df = df.copy()
    
    # Convert 'timestamp' column to datetime and sort the DataFrame
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Extract the date from timestamp
    df['date'] = df['timestamp'].dt.date
    
    # Generate a complete date range
    all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D').date
    
    # Get the first and last entries for each day
    daily_first = df.groupby('date').first().reindex(all_dates)
    daily_last = df.groupby('date').last().reindex(all_dates)
    
    # Ensure the index name is 'date'
    daily_first.index.name = 'date'
    daily_last.index.name = 'date'
    
    # Combine the first and last entries into a single DataFrame
    daily_stats = pd.DataFrame({
        'number_first': daily_first['number'],
        'timestamp_first': daily_first['timestamp'],
        'number_last': daily_last['number'],
        'timestamp_last': daily_last['timestamp']
    }, index=all_dates)
    
    # Forward-fill missing 'number_first' and 'timestamp_first' values
    daily_stats['number_first'] = daily_stats['number_first'].ffill()
    daily_stats['timestamp_first'] = daily_stats['timestamp_first'].ffill()
    
    # Backward-fill missing 'number_last' and 'timestamp_last' values
    daily_stats['number_last'] = daily_stats['number_last'].bfill()
    daily_stats['timestamp_last'] = daily_stats['timestamp_last'].bfill()
    
    # Calculate the time elapsed in hours
    daily_stats['hours_elapsed'] = (
        daily_stats['timestamp_last'] - daily_stats['timestamp_first']
    ).dt.total_seconds() / 3600
    
    # Calculate the clicks difference
    daily_stats['clicks_diff'] = daily_stats['number_last'] - daily_stats['number_first']
    
    # Handle cases where hours_elapsed is zero or negative
    daily_stats['daily_clicks'] = np.where(
        daily_stats['hours_elapsed'] > 0,
        (daily_stats['clicks_diff'] * (24 / daily_stats['hours_elapsed'])),
        0
    )
    
    # Replace infinities and NaNs with zeros
    daily_stats['daily_clicks'] = daily_stats['daily_clicks'].replace([np.inf, -np.inf], np.nan).fillna(0)
    
    # Keep only the 'daily_clicks' column
    daily_clicks = daily_stats[['daily_clicks']]
    
    # Set the index name
    daily_clicks.index.name = 'date'
    
    return daily_clicks

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
