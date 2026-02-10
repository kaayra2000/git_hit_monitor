from enum import Enum

import pandas as pd


class PlotGroupRange(Enum):
    """
    Gruplama aralıklarını tanımlayan enum.

    Her değer: (klasör_adı, pandas_frekansı, aralık_büyüklüğü)
    """
    AYLIK = ("aylik", "MS", 1)          # 1 aylık aralıklar
    CEYREKLIK = ("ceyreklik", "QS", 1)  # 1 çeyreklik (3 aylık) aralıklar
    YILLIK = ("yillik", "YS", 1)        # 1 yıllık aralıklar
    UC_YILLIK = ("3_yillik", "YS", 3)   # 3 yıllık aralıklar
    BES_YILLIK = ("5_yillik", "YS", 5)  # 5 yıllık aralıklar
    ON_YILLIK = ("10_yillik", "YS", 10) # 10 yıllık aralıklar

    @property
    def folder_name(self) -> str:
        return self.value[0]

    @property
    def freq(self) -> str:
        return self.value[1]

    @property
    def span(self) -> int:
        """Aralık büyüklüğü (ay veya yıl sayısı, frekansa bağlı)."""
        return self.value[2]

    # ------------------------------------------------------------------
    # Range splitting strategy (if/else yerine polimorfik yaklaşım)
    # ------------------------------------------------------------------

    def get_range_start(self, data_start: pd.Timestamp) -> pd.Timestamp:
        """Verinin başlangıcına göre ilk aralık başlangıcını hesaplar."""
        strategies = {
            'MS': lambda ts: ts.normalize().replace(day=1),
            'QS': lambda ts: ts.normalize().replace(
                month=((ts.month - 1) // 3) * 3 + 1, day=1
            ),
            'YS': lambda ts: ts.normalize().replace(month=1, day=1),
        }
        return strategies[self.freq](data_start)

    def get_next_range_start(self, current: pd.Timestamp) -> pd.Timestamp:
        """Bir sonraki aralık başlangıcını hesaplar."""
        offsets = {
            'MS': pd.DateOffset(months=self.span),
            'QS': pd.DateOffset(months=3 * self.span),
            'YS': pd.DateOffset(years=self.span),
        }
        return current + offsets[self.freq]

    def generate_file_name(
        self, range_start: pd.Timestamp, range_end: pd.Timestamp
    ) -> str:
        """
        Aralık için dosya adı üretir.

        Örnekler: 2024_08, 2024_Q3, 2024, 2023_2025
        """
        if self.freq == 'MS':
            return f"{range_start.year}_{range_start.month:02d}"
        if self.freq == 'QS':
            quarter = (range_start.month - 1) // 3 + 1
            return f"{range_start.year}_Q{quarter}"
        # YS
        if self.span == 1:
            return str(range_start.year)
        return f"{range_start.year}_{range_end.year - 1}"


class PlotPeriodType(Enum):
    """
    Grafik periyot tipi.

    Her değer: (görünen_ad, y_sütun, x_etiket, max_tick, pandas_freq, tıklama_sütun_adı)
    """
    GUNLUK = ("günlük", "daily_clicks", "Tarih", 30, "D", "daily_clicks")
    AYLIK = ("aylık", "monthly_clicks", "Ay", 12, "MS", "monthly_clicks")
    CEYREKLIK = ("çeyreklik", "quarterly_clicks", "Çeyrek", 12, "QS", "quarterly_clicks")
    YILLIK = ("yıllık", "yearly_clicks", "Yıl", 30, "YS", "yearly_clicks")

    @property
    def display_name(self) -> str:
        return self.value[0]

    @property
    def y_column(self) -> str:
        return self.value[1]

    @property
    def x_label(self) -> str:
        return self.value[2]

    @property
    def max_ticks(self) -> int:
        return self.value[3]

    @property
    def freq(self) -> str:
        return self.value[4]

    @property
    def column_name(self) -> str:
        return self.value[5]

    def capitalize(self) -> str:
        return self.display_name.capitalize()

    def __str__(self) -> str:
        return self.display_name

    def calculate_clicks(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Bu periyot için tıklama sayılarını hesaplar (geç import ile)."""
        from . import process_data_helper
        return process_data_helper.calculate_period_clicks(
            df, freq=self.freq, column_name=self.column_name
        )

    def get_group_ranges(self) -> list['PlotGroupRange']:
        """Bu periyot tipi için desteklenen gruplama aralıklarını döndürür."""
        mapping = {
            PlotPeriodType.GUNLUK: [
                PlotGroupRange.AYLIK,
                PlotGroupRange.CEYREKLIK,
                PlotGroupRange.YILLIK,
            ],
            PlotPeriodType.AYLIK: [
                PlotGroupRange.YILLIK,
                PlotGroupRange.UC_YILLIK,
            ],
            PlotPeriodType.CEYREKLIK: [
                PlotGroupRange.YILLIK,
                PlotGroupRange.BES_YILLIK,
            ],
            PlotPeriodType.YILLIK: [
                PlotGroupRange.UC_YILLIK,
                PlotGroupRange.ON_YILLIK,
            ],
        }
        return mapping.get(self, [])

    @property
    def folder_name(self) -> str:
        """Plot klasörü için ASCII uyumlu isim."""
        names = {
            PlotPeriodType.GUNLUK: "gunluk",
            PlotPeriodType.AYLIK: "aylik",
            PlotPeriodType.CEYREKLIK: "ceyreklik",
            PlotPeriodType.YILLIK: "yillik",
        }
        return names[self]