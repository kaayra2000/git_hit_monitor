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
    SAATLIK = ("saatlik", "hourly_clicks", "Saat", 24, "h", "hourly_clicks")
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

    def get_grouping_key(self, index: pd.DatetimeIndex) -> pd.Index | pd.Series:
        """
        Gruplama anahtarını (strategy pattern) döndürür.
        
        Args:
            index: Gruplanacak verinin DatetimeIndex'i.
            
        Returns:
            Gruplama için kullanılacak pandas Index veya Series (örn: index.month).
        """
        if self == AveragePeriodType.YILIN_CEYREKLERI:
            return index.quarter
        elif self == AveragePeriodType.YILIN_AYLARI:
            return index.month
        elif self == AveragePeriodType.AYIN_GUNLERI:
            return index.day
        elif self == AveragePeriodType.HAFTANIN_GUNLERI:
            return index.dayofweek
        elif self == AveragePeriodType.GUNUN_SAATLERI:
            return index.hour
        else:
            raise ValueError(f"Grouping strategy not implemented for {self}")

    def get_formatted_label(self, value: int) -> str:
        """
        Grup değeri için okunabilir etiket döndürür.
        
        Args:
            value: Grup değeri (örn: 1 [Ocak], 0 [Pazartesi]).
        """
        if self == AveragePeriodType.YILIN_AYLARI:
            months = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            return months.get(value, str(value))
        
        elif self == AveragePeriodType.HAFTANIN_GUNLERI:
            days = {
                0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 3: 'Perşembe', 4: 'Cuma', 5: 'Cumartesi', 6: 'Pazar'
            }
            return days.get(value, str(value))
        
        elif self == AveragePeriodType.YILIN_CEYREKLERI:
            return f"{value}. Çeyrek"
            
        elif self == AveragePeriodType.GUNUN_SAATLERI:
            return f"{value:02d}:00"
            
        return str(value)

    def calculate_clicks(self, df: 'pd.DataFrame') -> 'pd.DataFrame':
        """Bu periyot için tıklama sayılarını hesaplar (geç import ile)."""
        from . import process_data_helper
        return process_data_helper.calculate_period_clicks(
            df, freq=self.freq, column_name=self.column_name
        )

    def get_group_ranges(self) -> list['PlotGroupRange']:
        """Bu periyot tipi için desteklenen gruplama aralıklarını döndürür."""
        mapping = {
            PlotPeriodType.SAATLIK: [
                 # Saatlik veriler çok yoğun olacağı için şimdilik gruplama aralığı tanımlamıyoruz
                 # İlerde PlotGroupRange.GUNLUK eklenirse buraya eklenebilir.
            ],
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
            PlotPeriodType.SAATLIK: "saatlik",
            PlotPeriodType.GUNLUK: "gunluk",
            PlotPeriodType.AYLIK: "aylik",
            PlotPeriodType.CEYREKLIK: "ceyreklik",
            PlotPeriodType.YILLIK: "yillik",
        }
        return names[self]

    @property
    def generates_global_plot(self) -> bool:
        """
        Whether this period should produce a global (top-level) plot file.

        We intentionally keep hourly/`saatlik` out of automatic global plot
        generation because hourly data is dense and we prefer generating
        averages/range-based hourly plots only via the range/average generators.
        This keeps the behavior structural (controlled by the enum) rather than
        scattering 'if period == SAATLIK' checks across plotting code.
        """
        return self != PlotPeriodType.SAATLIK


class AveragePeriodType(Enum):
    """
    Ortalama istatistik periyot tipi.

    Her değer: (görünen_ad, y_sütun, x_etiket, kaynak_periyot_tipi)
    """
    YILIN_CEYREKLERI = ("yılın_çeyrekleri", "avg_clicks", "Çeyrek", PlotPeriodType.CEYREKLIK)
    YILIN_AYLARI = ("yılın_ayları", "avg_clicks", "Ay", PlotPeriodType.AYLIK)
    AYIN_GUNLERI = ("ayın_günleri", "avg_clicks", "Gün", PlotPeriodType.GUNLUK)
    HAFTANIN_GUNLERI = ("haftanın_günleri", "avg_clicks", "Haftanın Günü", PlotPeriodType.GUNLUK)
    GUNUN_SAATLERI = ("günün_saatleri", "avg_clicks", "Saat", PlotPeriodType.SAATLIK)

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
    def source_period_type(self) -> PlotPeriodType | None:
        return self.value[3]

    def capitalize(self) -> str:
        return self.display_name.replace("_", " ").title()

    def __str__(self) -> str:
        return self.display_name
    def get_grouping_key(self, index: pd.DatetimeIndex) -> pd.Index | pd.Series:
        """
        Gruplama anahtarını (strategy pattern) döndürür.
        
        Args:
            index: Gruplanacak verinin DatetimeIndex'i.
            
        Returns:
            Gruplama için kullanılacak pandas Index veya Series (örn: index.month).
        """
        if self == AveragePeriodType.YILIN_CEYREKLERI:
            return index.quarter
        elif self == AveragePeriodType.YILIN_AYLARI:
            return index.month
        elif self == AveragePeriodType.AYIN_GUNLERI:
            return index.day
        elif self == AveragePeriodType.HAFTANIN_GUNLERI:
            return index.dayofweek
        elif self == AveragePeriodType.GUNUN_SAATLERI:
            return index.hour
        else:
            raise ValueError(f"Grouping strategy not implemented for {self}")

    def get_formatted_label(self, value: int) -> str:
        """
        Grup değeri için okunabilir etiket döndürür.
        
        Args:
            value: Grup değeri (örn: 1 [Ocak], 0 [Pazartesi]).
        """
        if self == AveragePeriodType.YILIN_AYLARI:
            months = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            return months.get(value, str(value))
        
        elif self == AveragePeriodType.HAFTANIN_GUNLERI:
            days = {
                0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 3: 'Perşembe', 4: 'Cuma', 5: 'Cumartesi', 6: 'Pazar'
            }
            return days.get(value, str(value))
        
        elif self == AveragePeriodType.YILIN_CEYREKLERI:
            return f"{value}. Çeyrek"
            
        elif self == AveragePeriodType.GUNUN_SAATLERI:
            return f"{value:02d}:00"
            
        return str(value)
