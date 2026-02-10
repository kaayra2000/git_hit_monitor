"""
process_data_helper.py modülü için birim testleri.
Orantısal tıklama dağılımı mantığını doğrular (O(periyot) yaklaşımı).
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
import importlib.util

# Helpers modülünü import edebilmek için parent dizini path'e ekliyoruz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.process_data_helper import (
    _calculate_boundary_share,
    calculate_period_clicks,
    calculate_daily_clicks,
    calculate_monthly_clicks,
    calculate_quarterly_clicks,
    calculate_yearly_clicks
)


def _make_df(records: list[tuple[str, int]]) -> pd.DataFrame:
    """Test verisi için yardımcı fonksiyon."""
    return pd.DataFrame(records, columns=['timestamp', 'number'])


class TestCalculateBoundaryShare:
    """_calculate_boundary_share fonksiyonunun testleri."""

    def test_full_segment_in_target(self):
        """Tüm segment hedef aralık içinde → tam payı döndürmeli."""
        result = _calculate_boundary_share(
            click_a=100, click_b=115,
            time_a=pd.Timestamp('2024-08-11 10:00:00'),
            time_b=pd.Timestamp('2024-08-11 22:00:00'),
            target_start=pd.Timestamp('2024-08-11'),
            target_end=pd.Timestamp('2024-08-12')
        )
        assert abs(result - 15.0) < 0.001

    def test_proportional_split_left(self):
        """Sol periyodun payı → 14/15 oranında."""
        # 11 Ağustos 10:00 → 12 Ağustos 01:00 = 15 saat
        # 11 Ağustos payı: 14 saat → 14/15 * 15 = 14
        result = _calculate_boundary_share(
            click_a=100, click_b=115,
            time_a=pd.Timestamp('2024-08-11 10:00:00'),
            time_b=pd.Timestamp('2024-08-12 01:00:00'),
            target_start=pd.Timestamp('2024-08-11'),
            target_end=pd.Timestamp('2024-08-12')
        )
        assert abs(result - 14.0) < 0.001

    def test_proportional_split_right(self):
        """Sağ periyodun payı → 1/15 oranında."""
        result = _calculate_boundary_share(
            click_a=100, click_b=115,
            time_a=pd.Timestamp('2024-08-11 10:00:00'),
            time_b=pd.Timestamp('2024-08-12 01:00:00'),
            target_start=pd.Timestamp('2024-08-12'),
            target_end=pd.Timestamp('2024-08-13')
        )
        assert abs(result - 1.0) < 0.001

    def test_zero_click_diff(self):
        """Sıfır tıklama farkı → 0 döndürmeli."""
        result = _calculate_boundary_share(
            click_a=100, click_b=100,
            time_a=pd.Timestamp('2024-08-11 10:00:00'),
            time_b=pd.Timestamp('2024-08-12 01:00:00'),
            target_start=pd.Timestamp('2024-08-11'),
            target_end=pd.Timestamp('2024-08-12')
        )
        assert result == 0.0

    def test_no_overlap(self):
        """Hedef aralıkla kesişim yok → 0 döndürmeli."""
        result = _calculate_boundary_share(
            click_a=100, click_b=115,
            time_a=pd.Timestamp('2024-08-11 10:00:00'),
            time_b=pd.Timestamp('2024-08-11 22:00:00'),
            target_start=pd.Timestamp('2024-08-12'),
            target_end=pd.Timestamp('2024-08-13')
        )
        assert result == 0.0

    def test_month_boundary(self):
        """Ay sınırı geçişi → orantısal pay."""
        # 31 Ocak 12:00 → 1 Şubat 12:00 = 24 saat
        # Ocak payı (target: 1 Ocak → 1 Şubat): 12 saat → 12/24 * 24 = 12
        result = _calculate_boundary_share(
            click_a=1000, click_b=1024,
            time_a=pd.Timestamp('2024-01-31 12:00:00'),
            time_b=pd.Timestamp('2024-02-01 12:00:00'),
            target_start=pd.Timestamp('2024-01-01'),
            target_end=pd.Timestamp('2024-02-01')
        )
        assert abs(result - 12.0) < 0.001


class TestCalculatePeriodClicks:
    """calculate_period_clicks fonksiyonunun testleri."""

    def test_empty_dataframe(self):
        """Boş DataFrame → boş sonuç."""
        df = _make_df([])
        result = calculate_daily_clicks(df)
        assert result.empty

    def test_single_record(self):
        """Tek kayıt → boş sonuç (fark yok)."""
        df = _make_df([('2024-08-11 10:00:00', 100)])
        result = calculate_daily_clicks(df)
        assert result.empty

    def test_same_day_two_records(self):
        """Aynı gün iki kayıt → tüm fark o güne."""
        df = _make_df([
            ('2024-08-11 10:00:00', 100),
            ('2024-08-11 22:00:00', 130),
        ])
        result = calculate_daily_clicks(df)
        assert len(result) == 1
        assert abs(result.loc[pd.Timestamp('2024-08-11'), 'daily_clicks'] - 30.0) < 0.001

    def test_daily_cross_boundary(self):
        """İki gün arasında kayıt → orantısal dağılım."""
        df = _make_df([
            ('2024-08-11 10:00:00', 100),
            ('2024-08-12 01:00:00', 115),
        ])
        result = calculate_daily_clicks(df)
        # 11 Ağustos: iç=0, sağ_sınır=14 (14/15*15), toplam=14
        # 12 Ağustos: iç=0, sol_sınır=1 (1/15*15), toplam=1
        assert abs(result.loc[pd.Timestamp('2024-08-11'), 'daily_clicks'] - 14.0) < 0.001
        assert abs(result.loc[pd.Timestamp('2024-08-12'), 'daily_clicks'] - 1.0) < 0.001

    def test_three_days_proportional(self):
        """Üç gün, ortadaki günde tam iç tıklamalar."""
        df = _make_df([
            ('2024-08-10 18:00:00', 100),
            ('2024-08-11 06:00:00', 112),
            ('2024-08-11 18:00:00', 124),
            ('2024-08-12 06:00:00', 136),
        ])
        result = calculate_daily_clicks(df)
        # 10 Ağustos: iç=0, sağ_sınır payı (100→112, 6s/12s=0.5 → 6)
        # 11 Ağustos: iç=124-112=12, sol_sınır(100→112, 6s/12s=0.5→6), sağ_sınır(124→136, 6s/12s=0.5→6) = 24
        # 12 Ağustos: iç=0, sol_sınır(124→136, 6s/12s=0.5→6)
        assert abs(result.loc[pd.Timestamp('2024-08-10'), 'daily_clicks'] - 6.0) < 0.001
        assert abs(result.loc[pd.Timestamp('2024-08-11'), 'daily_clicks'] - 24.0) < 0.001
        assert abs(result.loc[pd.Timestamp('2024-08-12'), 'daily_clicks'] - 6.0) < 0.001

    def test_monthly_aggregation(self):
        """Aylık hesaplama birden çok kayıtla."""
        df = _make_df([
            ('2024-01-15 12:00:00', 100),
            ('2024-01-20 12:00:00', 200),
            ('2024-02-05 12:00:00', 350),
        ])
        result = calculate_monthly_clicks(df)
        assert 'monthly_clicks' in result.columns
        total = result['monthly_clicks'].sum()
        assert abs(total - 250.0) < 0.01  # 350 - 100 = 250

    def test_quarterly_calculation(self):
        """Çeyreklik hesaplama."""
        df = _make_df([
            ('2024-03-15 00:00:00', 1000),
            ('2024-06-15 00:00:00', 2000),
        ])
        result = calculate_quarterly_clicks(df)
        assert 'quarterly_clicks' in result.columns
        total = result['quarterly_clicks'].sum()
        assert abs(total - 1000.0) < 0.01

    def test_yearly_calculation(self):
        """Yıllık hesaplama."""
        df = _make_df([
            ('2024-06-01 00:00:00', 5000),
            ('2025-06-01 00:00:00', 15000),
        ])
        result = calculate_yearly_clicks(df)
        assert 'yearly_clicks' in result.columns
        total = result['yearly_clicks'].sum()
        assert abs(total - 10000.0) < 0.01

    def test_real_data_total_preserved(self):
        """Gerçek veriye benzer kayıtlar → toplam korunmalı."""
        df = _make_df([
            ('2024-08-26 11:40:15', 39697),
            ('2024-08-26 12:12:26', 39698),
            ('2024-08-26 13:20:49', 39700),
            ('2024-08-27 08:54:49', 39746),
            ('2024-08-27 18:17:07', 39788),
            ('2024-08-29 09:23:46', 39894),
        ])
        result = calculate_daily_clicks(df)
        total = result['daily_clicks'].sum()
        expected_total = 39894 - 39697  # 197
        assert abs(total - expected_total) < 0.01

    def test_index_is_datetime(self):
        """Sonuç indeksi DatetimeIndex olmalı."""
        df = _make_df([
            ('2024-08-11 10:00:00', 100),
            ('2024-08-12 01:00:00', 115),
        ])
        result = calculate_daily_clicks(df)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_month_boundary_correct_proportions(self):
        """Ay sınırı geçişinde doğru orantısal dağılım."""
        # 31 Ocak 12:00 → 1 Şubat 12:00 (24 saat süre)
        # Ocak payı: 12 saat, Şubat payı: 12 saat
        df = _make_df([
            ('2024-01-31 12:00:00', 1000),
            ('2024-02-01 12:00:00', 1024),
        ])
        result = calculate_monthly_clicks(df)
        assert abs(result.loc[pd.Timestamp('2024-01-01'), 'monthly_clicks'] - 12.0) < 0.001
        assert abs(result.loc[pd.Timestamp('2024-02-01'), 'monthly_clicks'] - 12.0) < 0.001

    def test_year_boundary_correct_proportions(self):
        """Yıl sınırı geçişinde doğru orantısal dağılım."""
        # 31 Aralık 20:00 → 1 Ocak 04:00 (8 saat)
        # 2024 payı: 4 saat, 2025 payı: 4 saat → eşit dağılım
        df = _make_df([
            ('2024-12-31 20:00:00', 10000),
            ('2025-01-01 04:00:00', 10080),
        ])
        result = calculate_yearly_clicks(df)
        assert abs(result.loc[pd.Timestamp('2024-01-01'), 'yearly_clicks'] - 40.0) < 0.001
        assert abs(result.loc[pd.Timestamp('2025-01-01'), 'yearly_clicks'] - 40.0) < 0.001


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
