import pandas as pd
import typing
from datetime import datetime
from collections import defaultdict

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


def _get_period_boundaries(start: datetime, end: datetime, freq: str) -> list[pd.Timestamp]:
    """
    Verilen zaman aralığı için periyot sınırlarını oluşturur.

    Args:
        start: Başlangıç zamanı
        end: Bitiş zamanı
        freq: Pandas frekans string'i ('D', 'MS', 'QS', 'YS')

    Returns:
        Periyot sınırlarının listesi (sıralı, tekrarsız)
    """
    # Frekansa göre başlangıcı normalize et
    if freq == 'D':
        norm_start = pd.Timestamp(start).normalize()
    elif freq == 'MS':
        norm_start = pd.Timestamp(start).normalize().replace(day=1)
    elif freq == 'QS':
        ts = pd.Timestamp(start).normalize()
        quarter_month = ((ts.month - 1) // 3) * 3 + 1
        norm_start = ts.replace(month=quarter_month, day=1)
    elif freq == 'YS':
        norm_start = pd.Timestamp(start).normalize().replace(month=1, day=1)
    else:
        raise ValueError(f"Desteklenmeyen frekans: {freq}")

    # Bitiş tarihini bir sonraki periyodun başlangıcına kadar genişlet
    norm_end = pd.Timestamp(end)

    # Periyot sınırlarını oluştur
    boundaries = pd.date_range(start=norm_start, end=norm_end + pd.DateOffset(**_freq_to_offset(freq)), freq=freq)

    # Sadece start-end aralığını kapsayan sınırları al
    boundaries = boundaries[boundaries <= norm_end + pd.DateOffset(**_freq_to_offset(freq))]

    return sorted(boundaries.tolist())


def _freq_to_offset(freq: str) -> dict:
    """Frekans string'ini DateOffset parametresine dönüştürür."""
    mapping = {
        'D': {'days': 1},
        'MS': {'months': 1},
        'QS': {'months': 3},
        'YS': {'years': 1},
    }
    return mapping[freq]


def distribute_clicks_proportionally(
    click_start: float,
    click_end: float,
    time_start: pd.Timestamp,
    time_end: pd.Timestamp,
    freq: str
) -> dict[pd.Timestamp, float]:
    """
    İki ardışık kayıt arasındaki tıklama farkını, periyot sınırlarına göre
    orantısal olarak dağıtır.

    Örnek: 11 Ağustos 10:00 → 12 Ağustos 01:00 arası 15 tıklama farkı varsa,
    14/15'i 11 Ağustos'a, 1/15'i 12 Ağustos'a yazılır.

    Args:
        click_start: Başlangıç kayıt tıklama sayısı
        click_end: Bitiş kayıt tıklama sayısı
        time_start: Başlangıç zamanı
        time_end: Bitiş zamanı
        freq: Periyot frekansı ('D', 'MS', 'QS', 'YS')

    Returns:
        Her periyot başlangıç zamanı -> o periyoda düşen tıklama miktarı
    """
    click_diff = click_end - click_start
    total_seconds = (time_end - time_start).total_seconds()

    if total_seconds <= 0 or click_diff <= 0:
        return {}

    # Periyot sınırlarını oluştur
    boundaries = _get_period_boundaries(time_start, time_end, freq)

    # time_start ve time_end arasındaki zaman dilimlerini periyotlara böl
    result: dict[pd.Timestamp, float] = {}

    for i in range(len(boundaries) - 1):
        period_start_boundary = boundaries[i]
        period_end_boundary = boundaries[i + 1]

        # Bu periyotta geçen sürenin başlangıcı ve bitişi
        segment_start = max(time_start, period_start_boundary)
        segment_end = min(time_end, period_end_boundary)

        if segment_start >= segment_end:
            continue

        segment_seconds = (segment_end - segment_start).total_seconds()
        ratio = segment_seconds / total_seconds
        clicks_for_period = click_diff * ratio

        if clicks_for_period > 0:
            result[period_start_boundary] = result.get(period_start_boundary, 0) + clicks_for_period

    return result


def calculate_period_clicks(df: pd.DataFrame, freq: str, column_name: str) -> pd.DataFrame:
    """
    Verilen frekansa göre tıklama sayılarını orantısal olarak hesaplar.
    Tüm periyot tipleri (günlük, aylık, çeyreklik, yıllık) için ortak fonksiyon.

    Ardışık kayıt çiftleri üzerinden döner, her çift için
    distribute_clicks_proportionally çağırarak tıklamaları periyotlara dağıtır.

    Args:
        df: timestamp ve number sütunlarını içeren DataFrame
        freq: Pandas frekans string'i ('D' günlük, 'MS' aylık, 'QS' çeyreklik, 'YS' yıllık)
        column_name: Sonuç sütununun adı

    Returns:
        Periyot başlangıçları indeksli, tıklama sayılarını içeren DataFrame
    """
    if df.empty:
        result = pd.DataFrame(columns=[column_name])
        result.index.name = 'period_start'
        return result

    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    if len(df) < 2:
        result = pd.DataFrame(columns=[column_name])
        result.index.name = 'period_start'
        return result

    # Tüm periyotlara düşen tıklamaları topla
    period_clicks: dict[pd.Timestamp, float] = defaultdict(float)

    for i in range(len(df) - 1):
        row_start = df.iloc[i]
        row_end = df.iloc[i + 1]

        distributed = distribute_clicks_proportionally(
            click_start=row_start['number'],
            click_end=row_end['number'],
            time_start=pd.Timestamp(row_start['timestamp']),
            time_end=pd.Timestamp(row_end['timestamp']),
            freq=freq
        )

        for period_key, clicks in distributed.items():
            period_clicks[period_key] += clicks

    if not period_clicks:
        result = pd.DataFrame(columns=[column_name])
        result.index.name = 'period_start'
        return result

    # Tüm periyotları kapsayacak bir aralık oluştur (boş periyotlar da dahil)
    all_period_starts = _get_period_boundaries(
        df['timestamp'].min(), df['timestamp'].max(), freq
    )
    # Son sınır indeks olmaz, o yüzden sadece başlangıçları al
    # Periyot sınırlarından, veri aralığındaki periyot başlangıçlarını filtrele
    valid_starts = [b for b in all_period_starts if b <= df['timestamp'].max()]

    # Sonuç DataFrame oluştur
    result = pd.DataFrame(
        {column_name: [period_clicks.get(ps, 0.0) for ps in valid_starts]},
        index=pd.DatetimeIndex(valid_starts, name='period_start')
    )

    return result


def calculate_daily_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """Günlük tıklanma sayısını orantısal olarak hesaplar."""
    return calculate_period_clicks(df, freq='D', column_name='daily_clicks')


def calculate_monthly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """Aylık tıklanma sayısını orantısal olarak hesaplar."""
    return calculate_period_clicks(df, freq='MS', column_name='monthly_clicks')


def calculate_quarterly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """3 aylık tıklanma sayısını orantısal olarak hesaplar."""
    return calculate_period_clicks(df, freq='QS', column_name='quarterly_clicks')


def calculate_yearly_clicks(df: pd.DataFrame) -> pd.DataFrame:
    """Yıllık tıklanma sayısını orantısal olarak hesaplar."""
    return calculate_period_clicks(df, freq='YS', column_name='yearly_clicks')


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
