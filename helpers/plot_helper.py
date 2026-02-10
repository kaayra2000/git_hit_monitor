import pandas as pd
import matplotlib.pyplot as plt
import os
from abc import ABC, abstractmethod
from . import process_data_helper
import matplotlib.dates as mdates
import math
from .enum_helper import PlotPeriodType, PlotGroupRange, AveragePeriodType


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
# Bar Chart Plotter (Ortalama İstatistikler)
# ---------------------------------------------------------------------------

class BarGraphPlotter(GraphPlotter):
    """Sütun grafik çizen sınıf (Ortalama istatistikler için)."""

    def __init__(self, df: pd.DataFrame, title: str, avg_type: AveragePeriodType) -> None:
        super().__init__(df, title, avg_type.y_column, avg_type.x_label)
        self.avg_type = avg_type

    def plot(self, fig_name: str) -> None:
        # Veri yoksa çizme
        if self.df.empty:
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        
        x_values = self.df.index
        y_values = self.df[self.y_column]
        
        labels = self._get_xticklabels(x_values)
        
        # Bar chart çiz
        ax.bar(x_values, y_values, color='#4CAF50', edgecolor='black', alpha=0.7)
        
        # Ortalama değeri çizgi olarak da gösterebiliriz (opsiyonel)
        # Şimdilik sadece bar
        
        ax.set_xticks(x_values)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        self._set_common_properties(ax)
        plt.tight_layout()
        plt.savefig(f"{fig_name}.svg", format="svg")
        plt.close()

    def _get_xticklabels(self, x_values) -> list[str]:
        """Index değerlerini okunabilir etiketlere dönüştürür."""
        return [self.avg_type.get_formatted_label(val) for val in x_values]


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
        # Use the period's own policy to decide whether to generate a
        # top-level/global plot. This is structural: the enum controls the
        # behavior instead of ad-hoc checks here. For example, hourly
        # (`saatlik`) is intentionally excluded from global plot generation
        # because hourly data should be handled via range/average generators.
        if not period.generates_global_plot:
            continue

        period_df = period.calculate_clicks(df)
        if not period_df.empty:
            title = f"{period.capitalize()} Tıklanma Sayısı"
            fig_name = f"{period}_clicks"
            plot_graph(period_df, period, title, fig_name)
        else:
            print(f"No data available for {period} graph")

    os.chdir(old_dir)

    # 2. Ortalama İstatistik Grafikleri
    avg_plot_dir = os.path.join(plot_dir, 'ortalama')
    os.makedirs(avg_plot_dir, exist_ok=True)
    os.chdir(avg_plot_dir)

    for avg_type in AveragePeriodType:
        avg_df = process_data_helper.calculate_average_statistics(df, avg_type)
        if not avg_df.empty:
            title = f"Ortalama {avg_type.capitalize()} Tıklanma"
            fig_name = f"{avg_type.display_name}"
            
            plotter = BarGraphPlotter(avg_df, title, avg_type)
            plotter.plot(fig_name)
    
    os.chdir(old_dir)

    if generate_range_plots:
        generator = PlotRangeGenerator(df, base_plot_dir=plot_dir)
        generator.generate_all_range_plots()

        # 3. Ortalama İstatistik Aralık Plotları
        avg_generator = AverageStatsRangeGenerator(df, base_plot_dir=avg_plot_dir)
        avg_generator.generate_all_avg_range_plots()


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


class AverageStatsRangeGenerator:
    """
    Ortalama istatistikler için aralık bazlı plot üretici.
    
    Örn: 2024 yılı "günün saatleri" ortalaması.
         2024 Ocak ayı "günün saatleri" ortalaması.
    """

    def __init__(self, df: pd.DataFrame, base_plot_dir: str = 'plots/ortalama') -> None:
        self.df = df.copy()
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.base_plot_dir = base_plot_dir

    def generate_all_avg_range_plots(self) -> None:
        """Desteklenen tüm ortalama tipleri için aralık plotlarını üretir."""
        # Şimdilik sadece günün saatleri için implemente ediyoruz
        self.generate_avg_range_plots(AveragePeriodType.GUNUN_SAATLERI)

    def generate_avg_range_plots(self, avg_type: AveragePeriodType) -> None:
        """Tek bir ortalama tipi için tüm gruplama aralıklarındaki plotları üretir."""
        # Günün saatleri için Yıllık ve Aylık kırılımları destekle
        supported_ranges = []
        if avg_type == AveragePeriodType.GUNUN_SAATLERI:
            supported_ranges = [PlotGroupRange.YILLIK, PlotGroupRange.AYLIK]
        
        for group_range in supported_ranges:
            self._generate_plots_for_range(avg_type, group_range)

    def _generate_plots_for_range(self, avg_type: AveragePeriodType,
                                  group_range: PlotGroupRange) -> None:
        """Belirli bir gruplama aralığı için tüm alt-aralık plotlarını üretir."""
        # PlotRangeGenerator'ın range bölme mantığını tekrar kullan (dry violation accepted for independence)
        # Aslında PlotRangeGenerator metodunu static yapıp kullanabiliriz ama şimdilik duplication ok.
        # Alternatif: PlotRangeGenerator'dan türetebilirdik ama logic biraz farklı.
        
        for range_start, range_end in self._split_into_ranges(group_range):
            self._plot_single_range(avg_type, group_range,
                                    range_start, range_end)

    def _plot_single_range(self, avg_type: AveragePeriodType,
                           group_range: PlotGroupRange,
                           range_start: pd.Timestamp,
                           range_end: pd.Timestamp) -> None:
        """Tek bir alt-aralık için ortalama plot üretir."""
        filtered_df = process_data_helper.filter_dataframe_by_date_range(
            self.df, range_start, range_end
        )
        if filtered_df.empty:
            return

        avg_df = process_data_helper.calculate_average_statistics(filtered_df, avg_type)
        if avg_df.empty:
            return

        file_name = group_range.generate_file_name(range_start, range_end)
        
        # Folder structure: plots/ortalama/{avg_type_name}/{range_type_name}/
        # avg_type.display_name: "günün_saatleri"
        # group_range.folder_name: "yillik"
        dir_path = os.path.join(
            self.base_plot_dir, avg_type.display_name, group_range.folder_name
        )
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, file_name)
        title = f"Ortalama {avg_type.capitalize()} ({file_name})"
        
        plotter = BarGraphPlotter(avg_df, title, avg_type)
        plotter.plot(fig_name=file_path) # BarGraphPlotter.plot expects name without extension

    def _split_into_ranges(
        self, group_range: PlotGroupRange
    ) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Veri aralığını gruplama aralığına göre (start, end) çiftlerine böler."""
        ts = self.df['timestamp']
        if ts.empty:
            return []
            
        data_start = ts.min()
        data_end = ts.max()

        ranges: list[tuple[pd.Timestamp, pd.Timestamp]] = []
        current = group_range.get_range_start(data_start)

        while current <= data_end:
            range_end = group_range.get_next_range_start(current)
            ranges.append((current, range_end))
            current = range_end

        return ranges
