import pandas as pd
import typing
from dataclasses import dataclass

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
    data = sheet.get_all_values()

    if not data or data[0] == []:
        return pd.DataFrame(columns=['timestamp', 'number'])

    if data[0] != ['timestamp', 'number']:
        data.insert(0, ['timestamp', 'number'])

    df = pd.DataFrame(data[1:], columns=data[0])
    df['number'] = pd.to_numeric(df['number'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp', 'number'])
    df = df.sort_values('timestamp')
    return df


# ---------------------------------------------------------------------------
# Periyot sınır yardımcıları
# ---------------------------------------------------------------------------

def _get_period_start(timestamp: pd.Timestamp, freq: str) -> pd.Timestamp:
    """Verilen zaman damgası için ait olduğu periyodun başlangıcını döndürür."""
    if freq == 'D':
        return timestamp.normalize()
    elif freq == 'MS':
        return timestamp.normalize().replace(day=1)
    elif freq == 'QS':
        quarter_month = ((timestamp.month - 1) // 3) * 3 + 1
        return timestamp.normalize().replace(month=quarter_month, day=1)
    elif freq == 'YS':
        return timestamp.normalize().replace(month=1, day=1)
    else:
        raise ValueError(f"Desteklenmeyen frekans: {freq}")


def _get_period_end(period_start: pd.Timestamp, freq: str) -> pd.Timestamp:
    """Verilen periyot başlangıcı için periyodun bitişini döndürür."""
    offsets = {
        'D': pd.DateOffset(days=1),
        'MS': pd.DateOffset(months=1),
        'QS': pd.DateOffset(months=3),
        'YS': pd.DateOffset(years=1),
    }
    return period_start + offsets[freq]


# ---------------------------------------------------------------------------
# Orantısal sınır hesaplama
# ---------------------------------------------------------------------------

def _calculate_boundary_share(
    click_a: float,
    click_b: float,
    time_a: pd.Timestamp,
    time_b: pd.Timestamp,
    target_start: pd.Timestamp,
    target_end: pd.Timestamp
) -> float:
    """
    İki kayıt arasındaki tıklama farkının, belirli bir zaman aralığına
    düşen orantısal payını hesaplar.

    Args:
        click_a: İlk kaydın tıklama sayısı
        click_b: İkinci kaydın tıklama sayısı
        time_a: İlk kaydın zamanı
        time_b: İkinci kaydın zamanı
        target_start: Hedef zaman aralığının başlangıcı
        target_end: Hedef zaman aralığının bitişi

    Returns:
        Hedef aralığa düşen tıklama miktarı
    """
    click_diff = click_b - click_a
    total_seconds = (time_b - time_a).total_seconds()

    if total_seconds <= 0 or click_diff <= 0:
        return 0.0

    segment_start = max(time_a, target_start)
    segment_end = min(time_b, target_end)

    if segment_start >= segment_end:
        return 0.0

    segment_seconds = (segment_end - segment_start).total_seconds()
    return click_diff * (segment_seconds / total_seconds)


# ---------------------------------------------------------------------------
# Komşu periyot bulma
# ---------------------------------------------------------------------------

def _find_prev_data_period(period_groups: pd.DataFrame, current_index: int) -> pd.Series | None:
    """Geriye doğru verisi olan ilk periyodu bulur."""
    for j in range(current_index - 1, -1, -1):
        row = period_groups.iloc[j]
        if not pd.isna(row['last_time']):
            return row
    return None


def _find_next_data_period(period_groups: pd.DataFrame, current_index: int) -> pd.Series | None:
    """İleriye doğru verisi olan ilk periyodu bulur."""
    for j in range(current_index + 1, len(period_groups)):
        row = period_groups.iloc[j]
        if not pd.isna(row['first_time']):
            return row
    return None


# ---------------------------------------------------------------------------
# Periyot tıklama hesaplayıcıları (Strategy Pattern)
# ---------------------------------------------------------------------------

def _estimate_from_overall_trend(
    df: pd.DataFrame,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
    anchor_time: pd.Timestamp | None = None,
    use_anchor_as_start: bool = True
) -> float:
    """
    Genel veri trendinden (son - ilk) orantısal tahmin yapar.

    Args:
        df: Tüm veri DataFrame'i
        period_start: Periyot başlangıcı
        period_end: Periyot bitişi
        anchor_time: Bilinen komşu kaydın zamanı (segment sınırı olarak kullanılır)
        use_anchor_as_start: True ise anchor sol sınır, False ise sağ sınır olur
    """
    overall_diff = df['number'].iloc[-1] - df['number'].iloc[0]
    overall_total_sec = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds()

    if overall_total_sec <= 0 or overall_diff <= 0:
        return 0.0

    if anchor_time is not None:
        if use_anchor_as_start:
            seg_start = max(anchor_time, period_start)
            seg_end = period_end
        else:
            seg_start = period_start
            seg_end = min(anchor_time, period_end)
    else:
        seg_start = period_start
        seg_end = period_end

    if seg_end <= seg_start:
        return 0.0

    seg_sec = (seg_end - seg_start).total_seconds()
    return overall_diff * (seg_sec / overall_total_sec)


def _calculate_empty_period_clicks(
    df: pd.DataFrame,
    period_groups: pd.DataFrame,
    index: int,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp
) -> float:
    """
    Verisi olmayan (boş) bir periyodun tıklama sayısını hesaplar.

    Komşu durumuna göre strateji seçer:
    - Her iki komşu var → aradaki orantısal pay
    - Sadece sonraki var → genel trendden sağ sınır payı
    - Sadece önceki var → genel trendden sol sınır payı
    - Hiçbiri yok → genel trendden toplam fark
    """
    prev_data = _find_prev_data_period(period_groups, index)
    next_data = _find_next_data_period(period_groups, index)

    has_prev = prev_data is not None
    has_next = next_data is not None

    if has_prev and has_next:
        return _calculate_boundary_share(
            click_a=prev_data['last_number'],
            click_b=next_data['first_number'],
            time_a=prev_data['last_time'],
            time_b=next_data['first_time'],
            target_start=period_start,
            target_end=period_end
        )

    if not has_prev and has_next:
        return _estimate_from_overall_trend(
            df, period_start, period_end,
            anchor_time=next_data['first_time'],
            use_anchor_as_start=False
        )

    if has_prev and not has_next:
        return _estimate_from_overall_trend(
            df, period_start, period_end,
            anchor_time=prev_data['last_time'],
            use_anchor_as_start=True
        )

    # İkisi de None → genel fark
    return max(0.0, df['number'].iloc[-1] - df['number'].iloc[0])


def _calculate_data_period_clicks(
    period_groups: pd.DataFrame,
    index: int,
    row: pd.Series,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp
) -> float:
    """
    Verisi olan bir periyodun tıklama sayısını hesaplar.

    Formül: iç_tıklamalar + sol_sınır_payı + sağ_sınır_payı
    """
    internal_clicks = max(0.0, row['last_number'] - row['first_number'])

    left_share = _compute_left_boundary(period_groups, index, row, period_start, period_end)
    right_share = _compute_right_boundary(period_groups, index, row, period_start, period_end)

    return internal_clicks + left_share + right_share


def _compute_left_boundary(
    period_groups: pd.DataFrame,
    index: int,
    row: pd.Series,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp
) -> float:
    """Önceki periyodun son kaydından bu periyodun ilk kaydına olan sınır payını hesaplar."""
    prev_row = _find_prev_data_period(period_groups, index)
    if prev_row is None:
        return 0.0

    return _calculate_boundary_share(
        click_a=prev_row['last_number'],
        click_b=row['first_number'],
        time_a=prev_row['last_time'],
        time_b=row['first_time'],
        target_start=period_start,
        target_end=period_end
    )


def _compute_right_boundary(
    period_groups: pd.DataFrame,
    index: int,
    row: pd.Series,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp
) -> float:
    """Bu periyodun son kaydından sonraki periyodun ilk kaydına olan sınır payını hesaplar."""
    next_row = _find_next_data_period(period_groups, index)
    if next_row is None:
        return 0.0

    return _calculate_boundary_share(
        click_a=row['last_number'],
        click_b=next_row['first_number'],
        time_a=row['last_time'],
        time_b=next_row['first_time'],
        target_start=period_start,
        target_end=period_end
    )


# ---------------------------------------------------------------------------
# Ana hesaplama fonksiyonu
# ---------------------------------------------------------------------------

def _create_empty_result(column_name: str) -> pd.DataFrame:
    """Boş sonuç DataFrame'i oluşturur."""
    result = pd.DataFrame(columns=[column_name])
    result.index.name = 'period_start'
    return result


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame'i hesaplama için hazırlar: kopyalar, dönüştürür, sıralar."""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df


def _build_period_groups(df: pd.DataFrame, freq: str) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Periyot gruplarını oluşturur ve tüm periyotları kapsayan aralığı döndürür."""
    df['period'] = df['timestamp'].apply(lambda t: _get_period_start(t, freq))

    period_groups = df.groupby('period').agg(
        first_time=('timestamp', 'first'),
        last_time=('timestamp', 'last'),
        first_number=('number', 'first'),
        last_number=('number', 'last')
    ).sort_index()

    all_periods = pd.date_range(
        start=period_groups.index.min(),
        end=period_groups.index.max(),
        freq=freq
    )

    period_groups = period_groups.reindex(all_periods)
    return period_groups, all_periods


def calculate_period_clicks(df: pd.DataFrame, freq: str, column_name: str) -> pd.DataFrame:
    """
    Verilen frekansa göre tıklama sayılarını orantısal olarak hesaplar.
    Tüm periyot tipleri (günlük, aylık, çeyreklik, yıllık) için ortak fonksiyon.

    Her periyot için sadece 4 değere bakılır (O(periyot_sayısı) karmaşıklık):
    1. Önceki periyodun son kaydı (prev_last)
    2. Bu periyodun ilk kaydı (curr_first)
    3. Bu periyodun son kaydı (curr_last)
    4. Sonraki periyodun ilk kaydı (next_first)

    Periyot tıklaması = iç_tıklamalar + sol_sınır_payı + sağ_sınır_payı

    Args:
        df: timestamp ve number sütunlarını içeren DataFrame
        freq: Pandas frekans string'i ('D', 'MS', 'QS', 'YS')
        column_name: Sonuç sütununun adı

    Returns:
        Periyot başlangıçları indeksli, tıklama sayılarını içeren DataFrame
    """
    if df.empty or len(df) < 2:
        return _create_empty_result(column_name)

    df = _prepare_dataframe(df)

    if len(df) < 2:
        return _create_empty_result(column_name)

    period_groups, all_periods = _build_period_groups(df, freq)

    clicks_list = []
    for i, period_start in enumerate(all_periods):
        row = period_groups.loc[period_start]
        period_end = _get_period_end(period_start, freq)

        if pd.isna(row['first_time']):
            clicks = _calculate_empty_period_clicks(
                df, period_groups, i, period_start, period_end
            )
        else:
            clicks = _calculate_data_period_clicks(
                period_groups, i, row, period_start, period_end
            )

        clicks_list.append(clicks)

    return pd.DataFrame(
        {column_name: clicks_list},
        index=pd.DatetimeIndex(all_periods, name='period_start')
    )


# ---------------------------------------------------------------------------
# Periyot bazlı public API
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tarih aralığı filtreleme
# ---------------------------------------------------------------------------

def filter_dataframe_by_date_range(
    df: pd.DataFrame,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp
) -> pd.DataFrame:
    """
    DataFrame'i belirtilen tarih aralığına [start_date, end_date) göre filtreler.

    Args:
        df: timestamp sütunu içeren DataFrame
        start_date: Başlangıç tarihi (dahil)
        end_date: Bitiş tarihi (hariç)

    Returns:
        Filtrelenmiş DataFrame
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    mask = (df['timestamp'] >= start_date) & (df['timestamp'] < end_date)
    return df.loc[mask].reset_index(drop=True)