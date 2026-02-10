import pandas as pd
import matplotlib.pyplot as plt
import os
from abc import ABC, abstractmethod
from . import process_data_helper
import matplotlib.dates as mdates
import math
from .enum_helper import PlotPeriodType, PlotGroupRange


# ---------------------------------------------------------------------------
# Grafik çizici hierarchy (Open/Closed Principle)
# ---------------------------------------------------------------------------

class GraphPlotter(ABC):
    """Grafik çizici temel sınıfı."""

    def __init__(self, df: pd.DataFrame, title: str, y_column: str,
                 x_label: str, max_ticks: int = 10) -> None:
        self.df = df
        self.title = title
        self.y_column = y_column
        self.x_label = x_label
        self.max_ticks = max_ticks

    @abstractmethod
    def plot(self, fig_name: str) -> None:
        pass

    def _set_common_properties(self, ax) -> None:
        ax.set_title(self.title)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel('Tıklanma Sayısı')
        ax.grid(True)
        plt.tight_layout()


class LineGraphPlotter(GraphPlotter):
    """Çizgi grafik çizen sınıf."""

    def plot(self, fig_name: str, save_format: str = "svg") -> None:
        fig, ax = plt.subplots(figsize=(12, 6))

        self._ensure_datetime_index()
        date_numbers = mdates.date2num(self.df.index)

        self._draw_data(ax, date_numbers)
        self._draw_mean_line(ax)
        self._configure_x_ticks(ax, date_numbers)

        ax.xaxis_date()
        ax.legend()
        self._set_common_properties(ax)
        plt.tight_layout()
        plt.savefig(f"{fig_name}.{save_format}", format=save_format)
        plt.close()

    def _ensure_datetime_index(self) -> None:
        """İndeksi datetime tipine dönüştürür."""
        if isinstance(self.df.index, pd.PeriodIndex):
            self.df.index = self.df.index.to_timestamp()
        elif not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)

    def _draw_data(self, ax, date_numbers) -> None:
        """Veri noktalarını çizer (tek veri = bar, çoklu = line)."""
        if len(self.df) > 1:
            ax.plot(date_numbers, self.df[self.y_column],
                    marker='o', label='Veri')
        else:
            ax.bar(date_numbers, self.df[self.y_column],
                   width=20, label='Veri')

    def _draw_mean_line(self, ax) -> None:
        """Ortalama çizgisini ekler."""
        mean_value = self.df[self.y_column].mean()
        ax.axhline(y=mean_value, color='r', linestyle='--',
                   linewidth=2, label='Ortalama')

    def _configure_x_ticks(self, ax, date_numbers) -> None:
        """X ekseni etiketlerini ayarlar."""
        total_points = len(self.df)
        interval = math.ceil(total_points / self.max_ticks)

        tick_indices = range(0, total_points, interval)
        tick_values = [date_numbers[i] for i in tick_indices]
        tick_labels = [self.df.index[i].strftime('%Y-%m-%d')
                       for i in tick_indices]

        ax.set_xticks(tick_values)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')


class YearlyGraphPlotter(LineGraphPlotter):
    """Yıllık grafik çizen sınıf (etiketler döndürülmez)."""

    def __init__(self, df: pd.DataFrame, title: str) -> None:
        super().__init__(df, title, 'yearly_clicks', 'Yıl', 30)

    def plot(self, fig_name: str) -> None:
        super().plot(fig_name)
        plt.xticks(rotation=0)


# ---------------------------------------------------------------------------
# Fabrika (Single Responsibility – plotter oluşturma)
# ---------------------------------------------------------------------------

class GraphFactory:
    """PlotPeriodType'a göre uygun GraphPlotter oluşturur."""

    @staticmethod
    def create_plotter(period: PlotPeriodType, df: pd.DataFrame,
                       title: str) -> GraphPlotter:
        if period == PlotPeriodType.YILLIK:
            return YearlyGraphPlotter(df, title)
        return LineGraphPlotter(
            df, title, period.y_column, period.x_label, period.max_ticks
        )


# ---------------------------------------------------------------------------
# Tek periyot plot fonksiyonu
# ---------------------------------------------------------------------------

def plot_graph(df: pd.DataFrame, period: PlotPeriodType,
               title: str, fig_name: str) -> None:
    """Belirtilen periyoda göre grafik çizer."""
    plotter = GraphFactory.create_plotter(period, df, title)
    plotter.plot(fig_name)


# ---------------------------------------------------------------------------
# Tüm plotlar (mevcut + aralık bazlı)
# ---------------------------------------------------------------------------

def plot_all_graphs(df: pd.DataFrame, plot_dir: str = 'plots',
                    generate_range_plots: bool = False) -> None:
    """
    Tüm periyotlar için grafikleri çizer ve kaydeder.

    Args:
        df: Çizilecek veriyi içeren DataFrame
        plot_dir: Grafiklerin kaydedileceği dizin
        generate_range_plots: True ise aralık bazlı plotları da üretir
    """
    os.makedirs(plot_dir, exist_ok=True)

    old_dir = os.getcwd()
    os.chdir(plot_dir)

    for period in PlotPeriodType:
        period_df = period.calculate_clicks(df)
        if not period_df.empty:
            title = f"{period.capitalize()} Tıklanma Sayısı"
            fig_name = f"{period}_clicks"
            plot_graph(period_df, period, title, fig_name)
        else:
            print(f"No data available for {period} graph")

    os.chdir(old_dir)

    if generate_range_plots:
        generator = PlotRangeGenerator(df, base_plot_dir=plot_dir)
        generator.generate_all_range_plots()


# ---------------------------------------------------------------------------
# Aralık bazlı plot üretici (Single Responsibility)
# ---------------------------------------------------------------------------

class PlotRangeGenerator:
    """
    Belirli aralıklara göre plot dosyaları üreten sınıf.

    Her periyot tipi için ilgili gruplama aralıklarına göre veriyi böler
    ve ayrı plot dosyaları oluşturur.
    """

    def __init__(self, df: pd.DataFrame, base_plot_dir: str = 'plots') -> None:
        self.df = df.copy()
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.base_plot_dir = base_plot_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all_range_plots(self) -> None:
        """Tüm periyot tipleri için tüm aralık plotlarını üretir."""
        for period in PlotPeriodType:
            self.generate_range_plots(period)

    def generate_range_plots(self, period: PlotPeriodType) -> None:
        """Tek bir periyot tipi için tüm gruplama aralıklarındaki plotları üretir."""
        for group_range in period.get_group_ranges():
            self._generate_plots_for_range(period, group_range)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _generate_plots_for_range(self, period: PlotPeriodType,
                                  group_range: PlotGroupRange) -> None:
        """Belirli bir gruplama aralığı için tüm alt-aralık plotlarını üretir."""
        for range_start, range_end in self._split_into_ranges(group_range):
            self._plot_single_range(period, group_range,
                                    range_start, range_end)

    def _plot_single_range(self, period: PlotPeriodType,
                           group_range: PlotGroupRange,
                           range_start: pd.Timestamp,
                           range_end: pd.Timestamp) -> None:
        """Tek bir alt-aralık için plot üretir."""
        filtered_df = process_data_helper.filter_dataframe_by_date_range(
            self.df, range_start, range_end
        )
        if filtered_df.empty or len(filtered_df) < 2:
            return

        period_df = period.calculate_clicks(filtered_df)
        if period_df.empty:
            return

        file_name = group_range.generate_file_name(range_start, range_end)
        dir_path = os.path.join(
            self.base_plot_dir, period.folder_name, group_range.folder_name
        )
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, file_name)
        title = f"{period.capitalize()} Tıklanma ({file_name})"
        plot_graph(period_df, period, title, file_path)

    def _split_into_ranges(
        self, group_range: PlotGroupRange
    ) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Veri aralığını gruplama aralığına göre (start, end) çiftlerine böler."""
        ts = self.df['timestamp']
        data_start = ts.min()
        data_end = ts.max()

        ranges: list[tuple[pd.Timestamp, pd.Timestamp]] = []
        current = group_range.get_range_start(data_start)

        while current <= data_end:
            range_end = group_range.get_next_range_start(current)
            ranges.append((current, range_end))
            current = range_end

        return ranges
