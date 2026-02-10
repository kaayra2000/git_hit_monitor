"""
PlotRangeGenerator ve ilgili enum'lar için birim testleri.
"""

import sys
import os
import pytest
import pandas as pd
import importlib.util
import shutil
import tempfile

# Helpers modülünü import edebilmek için parent dizini path'e ekliyoruz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.enum_helper import PlotGroupRange, PlotPeriodType
from helpers.process_data_helper import filter_dataframe_by_date_range


def _make_df(records: list[tuple[str, int]]) -> pd.DataFrame:
    """Test verisi için yardımcı fonksiyon."""
    return pd.DataFrame(records, columns=['timestamp', 'number'])


# =========================================================================
# PlotGroupRange Testleri
# =========================================================================

class TestPlotGroupRange:
    """PlotGroupRange enum testleri."""

    def test_folder_name(self):
        assert PlotGroupRange.AYLIK.folder_name == "aylik"
        assert PlotGroupRange.CEYREKLIK.folder_name == "ceyreklik"
        assert PlotGroupRange.YILLIK.folder_name == "yillik"
        assert PlotGroupRange.UC_YILLIK.folder_name == "3_yillik"
        assert PlotGroupRange.BES_YILLIK.folder_name == "5_yillik"
        assert PlotGroupRange.ON_YILLIK.folder_name == "10_yillik"

    def test_freq(self):
        assert PlotGroupRange.AYLIK.freq == "MS"
        assert PlotGroupRange.CEYREKLIK.freq == "QS"
        assert PlotGroupRange.YILLIK.freq == "YS"
        assert PlotGroupRange.UC_YILLIK.freq == "YS"

    def test_span(self):
        assert PlotGroupRange.AYLIK.span == 1
        assert PlotGroupRange.CEYREKLIK.span == 1
        assert PlotGroupRange.YILLIK.span == 1
        assert PlotGroupRange.UC_YILLIK.span == 3
        assert PlotGroupRange.BES_YILLIK.span == 5
        assert PlotGroupRange.ON_YILLIK.span == 10

    def test_get_range_start_monthly(self):
        ts = pd.Timestamp('2024-08-15 14:30:00')
        result = PlotGroupRange.AYLIK.get_range_start(ts)
        assert result == pd.Timestamp('2024-08-01')

    def test_get_range_start_quarterly(self):
        ts = pd.Timestamp('2024-08-15')
        result = PlotGroupRange.CEYREKLIK.get_range_start(ts)
        assert result == pd.Timestamp('2024-07-01')

    def test_get_range_start_yearly(self):
        ts = pd.Timestamp('2024-08-15')
        result = PlotGroupRange.YILLIK.get_range_start(ts)
        assert result == pd.Timestamp('2024-01-01')

    def test_get_next_range_start_monthly(self):
        current = pd.Timestamp('2024-08-01')
        result = PlotGroupRange.AYLIK.get_next_range_start(current)
        assert result == pd.Timestamp('2024-09-01')

    def test_get_next_range_start_quarterly(self):
        current = pd.Timestamp('2024-07-01')
        result = PlotGroupRange.CEYREKLIK.get_next_range_start(current)
        assert result == pd.Timestamp('2024-10-01')  # 3 ay sonra (1 çeyrek)

    def test_get_next_range_start_yearly(self):
        current = pd.Timestamp('2024-01-01')
        result = PlotGroupRange.UC_YILLIK.get_next_range_start(current)
        assert result == pd.Timestamp('2027-01-01')


# =========================================================================
# PlotGroupRange.generate_file_name Testleri
# =========================================================================

class TestGenerateFileName:
    """Dosya adı üretimi testleri."""

    def test_monthly_name(self):
        result = PlotGroupRange.AYLIK.generate_file_name(
            pd.Timestamp('2024-08-01'), pd.Timestamp('2024-09-01'))
        assert result == "2024_08"

    def test_quarterly_name(self):
        result = PlotGroupRange.CEYREKLIK.generate_file_name(
            pd.Timestamp('2024-07-01'), pd.Timestamp('2024-10-01'))
        assert result == "2024_Q3"

    def test_yearly_name(self):
        result = PlotGroupRange.YILLIK.generate_file_name(
            pd.Timestamp('2024-01-01'), pd.Timestamp('2025-01-01'))
        assert result == "2024"

    def test_multi_year_name(self):
        result = PlotGroupRange.UC_YILLIK.generate_file_name(
            pd.Timestamp('2023-01-01'), pd.Timestamp('2026-01-01'))
        assert result == "2023_2025"

    def test_five_year_name(self):
        result = PlotGroupRange.BES_YILLIK.generate_file_name(
            pd.Timestamp('2021-01-01'), pd.Timestamp('2026-01-01'))
        assert result == "2021_2025"

    def test_ten_year_name(self):
        result = PlotGroupRange.ON_YILLIK.generate_file_name(
            pd.Timestamp('2016-01-01'), pd.Timestamp('2026-01-01'))
        assert result == "2016_2025"


# =========================================================================
# PlotPeriodType Testleri
# =========================================================================

class TestPlotPeriodType:
    """PlotPeriodType enum testleri."""

    def test_display_name(self):
        assert str(PlotPeriodType.GUNLUK) == "günlük"
        assert str(PlotPeriodType.AYLIK) == "aylık"

    def test_y_column(self):
        assert PlotPeriodType.GUNLUK.y_column == "daily_clicks"
        assert PlotPeriodType.AYLIK.y_column == "monthly_clicks"
        assert PlotPeriodType.CEYREKLIK.y_column == "quarterly_clicks"
        assert PlotPeriodType.YILLIK.y_column == "yearly_clicks"

    def test_x_label(self):
        assert PlotPeriodType.GUNLUK.x_label == "Tarih"
        assert PlotPeriodType.YILLIK.x_label == "Yıl"

    def test_max_ticks(self):
        assert PlotPeriodType.GUNLUK.max_ticks == 30
        assert PlotPeriodType.AYLIK.max_ticks == 12

    def test_freq(self):
        assert PlotPeriodType.GUNLUK.freq == "D"
        assert PlotPeriodType.AYLIK.freq == "MS"
        assert PlotPeriodType.CEYREKLIK.freq == "QS"
        assert PlotPeriodType.YILLIK.freq == "YS"

    def test_folder_name(self):
        assert PlotPeriodType.GUNLUK.folder_name == "gunluk"
        assert PlotPeriodType.AYLIK.folder_name == "aylik"
        assert PlotPeriodType.CEYREKLIK.folder_name == "ceyreklik"
        assert PlotPeriodType.YILLIK.folder_name == "yillik"

    def test_gunluk_group_ranges(self):
        ranges = PlotPeriodType.GUNLUK.get_group_ranges()
        assert PlotGroupRange.AYLIK in ranges
        assert PlotGroupRange.CEYREKLIK in ranges
        assert PlotGroupRange.YILLIK in ranges
        assert len(ranges) == 3

    def test_aylik_group_ranges(self):
        ranges = PlotPeriodType.AYLIK.get_group_ranges()
        assert PlotGroupRange.YILLIK in ranges
        assert PlotGroupRange.UC_YILLIK in ranges
        assert len(ranges) == 2

    def test_ceyreklik_group_ranges(self):
        ranges = PlotPeriodType.CEYREKLIK.get_group_ranges()
        assert PlotGroupRange.YILLIK in ranges
        assert PlotGroupRange.BES_YILLIK in ranges
        assert len(ranges) == 2

    def test_yillik_group_ranges(self):
        ranges = PlotPeriodType.YILLIK.get_group_ranges()
        assert PlotGroupRange.UC_YILLIK in ranges
        assert PlotGroupRange.ON_YILLIK in ranges
        assert len(ranges) == 2

    def test_capitalize(self):
        assert PlotPeriodType.GUNLUK.capitalize() == "Günlük"


# =========================================================================
# filter_dataframe_by_date_range Testleri
# =========================================================================

class TestFilterDataframeByDateRange:
    """filter_dataframe_by_date_range fonksiyonu testleri."""

    def test_basic_filter(self):
        df = _make_df([
            ('2024-01-15 12:00:00', 100),
            ('2024-02-15 12:00:00', 200),
            ('2024-03-15 12:00:00', 300),
        ])
        result = filter_dataframe_by_date_range(
            df, pd.Timestamp('2024-02-01'), pd.Timestamp('2024-03-01'))
        assert len(result) == 1
        assert result.iloc[0]['number'] == 200

    def test_empty_result(self):
        df = _make_df([('2024-01-15 12:00:00', 100)])
        result = filter_dataframe_by_date_range(
            df, pd.Timestamp('2024-06-01'), pd.Timestamp('2024-07-01'))
        assert result.empty

    def test_start_inclusive_end_exclusive(self):
        df = _make_df([
            ('2024-02-01 00:00:00', 100),
            ('2024-03-01 00:00:00', 200),
        ])
        result = filter_dataframe_by_date_range(
            df, pd.Timestamp('2024-02-01'), pd.Timestamp('2024-03-01'))
        assert len(result) == 1
        assert result.iloc[0]['number'] == 100

    def test_full_range(self):
        df = _make_df([
            ('2024-01-15 12:00:00', 100),
            ('2024-02-15 12:00:00', 200),
            ('2024-03-15 12:00:00', 300),
        ])
        result = filter_dataframe_by_date_range(
            df, pd.Timestamp('2024-01-01'), pd.Timestamp('2024-04-01'))
        assert len(result) == 3


# =========================================================================
# Range bölme mantığı testleri (PlotGroupRange metodları kullanarak)
# =========================================================================

class TestSplitIntoRanges:
    """Aralık bölme mantığı testleri."""

    def _split(self, data_start, data_end, group_range):
        """PlotRangeGenerator._split_into_ranges mantığı."""
        ranges = []
        current = group_range.get_range_start(data_start)
        while current <= data_end:
            range_end = group_range.get_next_range_start(current)
            ranges.append((current, range_end))
            current = range_end
        return ranges

    def test_monthly_split(self):
        start = pd.Timestamp('2024-08-15')
        end = pd.Timestamp('2024-10-20')
        ranges = self._split(start, end, PlotGroupRange.AYLIK)
        assert len(ranges) == 3
        assert ranges[0] == (pd.Timestamp('2024-08-01'), pd.Timestamp('2024-09-01'))
        assert ranges[1] == (pd.Timestamp('2024-09-01'), pd.Timestamp('2024-10-01'))
        assert ranges[2] == (pd.Timestamp('2024-10-01'), pd.Timestamp('2024-11-01'))

    def test_quarterly_split(self):
        start = pd.Timestamp('2024-03-15')
        end = pd.Timestamp('2024-09-20')
        ranges = self._split(start, end, PlotGroupRange.CEYREKLIK)
        # CEYREKLIK span=1 → 1 çeyrek = 3 ay per aralık
        # Veri: Mart 2024 → Eylül 2024 → 3 çeyreklik aralık (Q1, Q2, Q3)
        assert len(ranges) == 3
        assert ranges[0] == (pd.Timestamp('2024-01-01'), pd.Timestamp('2024-04-01'))
        assert ranges[1] == (pd.Timestamp('2024-04-01'), pd.Timestamp('2024-07-01'))
        assert ranges[2] == (pd.Timestamp('2024-07-01'), pd.Timestamp('2024-10-01'))

    def test_yearly_split(self):
        start = pd.Timestamp('2023-06-15')
        end = pd.Timestamp('2025-03-20')
        ranges = self._split(start, end, PlotGroupRange.YILLIK)
        assert len(ranges) == 3
        assert ranges[0] == (pd.Timestamp('2023-01-01'), pd.Timestamp('2024-01-01'))

    def test_multi_year_split(self):
        start = pd.Timestamp('2020-06-15')
        end = pd.Timestamp('2025-03-20')
        ranges = self._split(start, end, PlotGroupRange.UC_YILLIK)
        assert len(ranges) == 2
        assert ranges[0] == (pd.Timestamp('2020-01-01'), pd.Timestamp('2023-01-01'))
        assert ranges[1] == (pd.Timestamp('2023-01-01'), pd.Timestamp('2026-01-01'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
