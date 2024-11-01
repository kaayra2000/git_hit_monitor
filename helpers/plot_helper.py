import pandas as pd
import matplotlib.pyplot as plt
import os
from abc import ABC, abstractmethod
from . import process_data_helper
import matplotlib.dates as mdates
import math
from .enum_helper import PlotPeriodType

class GraphPlotter(ABC):
    def __init__(self, df: pd.DataFrame, title: str, y_column: str, x_label: str, max_ticks: int = 10) -> None:
        """
        GraphPlotter sınıfının yapıcı metodu.

        Args:
            df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
            title (str): Grafiğin başlığı
            y_column (str): Y ekseninde gösterilecek sütunun adı
            x_label (str): X ekseni etiketi

        Returns:
            None
        """
        self.df = df
        self.title = title
        self.y_column = y_column
        self.x_label = x_label
        self.max_ticks = max_ticks

    @abstractmethod
    def plot(self, fig_name: str) -> None:
        """
        Grafiği çizen soyut metot.

        Args:
            fig_name (str): Kaydedilecek dosyanın adı

        Returns:
            None
        """
        pass

    def _set_common_properties(self, ax) -> None:
        """
        Grafik özelliklerini ayarlayan yardımcı metot.

        Args:
            ax: Matplotlib axes nesnesi

        Returns:
            None
        """
        ax.set_title(self.title)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel('Tıklanma Sayısı')
        ax.grid(True)
        plt.tight_layout()

class LineGraphPlotter(GraphPlotter):
    def plot(self, fig_name: str, save_format: str = "svg") -> None:
        fig, ax = plt.subplots(figsize=(12, 6))

        # İndeksin tipini kontrol et ve datetime tipine dönüştür
        if isinstance(self.df.index, pd.PeriodIndex):
            self.df.index = self.df.index.to_timestamp()
        elif not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)

        # İndeks değerlerini Matplotlib'in anlayacağı float tipine dönüştür
        date_numbers = mdates.date2num(self.df.index)

        if len(self.df) > 1:
            ax.plot(date_numbers, self.df[self.y_column], marker='o', label='Veri')
        else:
            ax.bar(date_numbers, self.df[self.y_column], width=20, label='Veri')  # width değerini periyoda göre ayarlayın

        # Ortalama değeri hesapla ve ortalama çizgisini ekle
        mean_value = self.df[self.y_column].mean()
        ax.axhline(y=mean_value, color='r', linestyle='--', linewidth=2, label='Ortalama')

        # Toplam veri noktası sayısını bulun
        total_points = len(self.df)

        # Interval'ı hesaplayın
        interval = math.ceil(total_points / self.max_ticks)

        # X ekseni etiketlerinin konumlarını belirleyin
        tick_indices = range(0, total_points, interval)
        tick_values = [date_numbers[i] for i in tick_indices]
        tick_labels = [self.df.index[i].strftime('%Y-%m-%d') for i in tick_indices]

        # X ekseni etiketlerini ayarlayın
        ax.set_xticks(tick_values)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')

        # Otomatik tarih formatlamasını etkinleştir
        ax.xaxis_date()

        # Legend'i göster
        ax.legend()

        self._set_common_properties(ax)
        plt.tight_layout()
        plt.savefig(fig_name + f".{save_format}", format=save_format)
        plt.close()
class YearlyGraphPlotter(LineGraphPlotter):
    def __init__(self, df: pd.DataFrame, title: str) -> None:
        """
        YearlyGraphPlotter sınıfının yapıcı metodu.

        Args:
            df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
            title (str): Grafiğin başlığı

        Returns:
            None
        """
        super().__init__(df, title, 'yearly_clicks', 'Yıl', 30)

    def plot(self, fig_name: str) -> None:
        """
        Yıllık grafiği çizen metot.

        Args:
            fig_name (str): Kaydedilecek dosyanın adı

        Returns:
            None
        """
        super().plot(fig_name)
        plt.xticks(rotation=0)  # Yıl etiketlerini döndürmeye gerek yok

class GraphFactory:
    @staticmethod
    def create_plotter(period: PlotPeriodType, df: pd.DataFrame, title: str) -> GraphPlotter:
        """
        Belirtilen periyoda göre uygun GraphPlotter nesnesini oluşturan fabrika metodu.

        Args:
            period (PlotPeriodType): Grafik periyodu ('günlük', 'aylık', 'çeyreklik', 'yıllık')
            df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
            title (str): Grafiğin başlığı

        Returns:
            GraphPlotter: Oluşturulan GraphPlotter nesnesi
        """
        plotters = {
            PlotPeriodType.GUNLUK: lambda: LineGraphPlotter(df, title, 'daily_clicks', 'Tarih', 30),
            PlotPeriodType.AYLIK: lambda: LineGraphPlotter(df, title, 'monthly_clicks', 'Ay', 12),
            PlotPeriodType.CEYREKLIK: lambda: LineGraphPlotter(df, title, 'quarterly_clicks', 'Çeyrek', 12),
            PlotPeriodType.YILLIK: lambda: YearlyGraphPlotter(df, title, )
        }
        return plotters.get(period, lambda: None)()

def plot_graph(df: pd.DataFrame, period: str, title: str, fig_name: str) -> None:
    """
    Belirtilen periyoda göre grafik çizen fonksiyon.

    Args:
        df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
        period (str): Grafik periyodu
        title (str): Grafiğin başlığı
        fig_name (str): Kaydedilecek dosyanın adı

    Returns:
        None
    """
    plotter = GraphFactory.create_plotter(period, df, title)
    if plotter:
        plotter.plot(fig_name)
    else:
        raise ValueError(f"Invalid period: {period}")

def plot_all_graphs(df: pd.DataFrame, plot_dir: str = 'plots') -> None:
    """
    Tüm periyotlar için grafikleri çizen ve kaydeden fonksiyon.

    Args:
        df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
        plot_dir (str): Grafiklerin kaydedileceği dizin, varsayılan değeri 'plots'

    Returns:
        None
    """
    # Eğer belirtilen dizin yoksa, yeni bir dizin oluştur
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    # Mevcut çalışma dizinini kaydet
    old_dir = os.getcwd()
    # Çalışma dizinini grafiklerin kaydedileceği dizine değiştir
    os.chdir(plot_dir)
    
    # Farklı periyotlar için hesaplama fonksiyonlarını tanımla
    periods = {
        PlotPeriodType.GUNLUK: process_data_helper.calculate_daily_clicks,
        PlotPeriodType.AYLIK: process_data_helper.calculate_monthly_clicks,
        PlotPeriodType.CEYREKLIK: process_data_helper.calculate_quarterly_clicks,
        PlotPeriodType.YILLIK: process_data_helper.calculate_yearly_clicks
    }
    
    # Her bir periyot için grafik çiz
    for period, calculate_func in periods.items():
        # İlgili periyot için tıklanma sayılarını hesapla
        period_df = calculate_func(df)
        # Eğer hesaplanan DataFrame boş değilse grafik çiz
        if not period_df.empty:
            # Grafik başlığını oluştur
            title = f"{period.capitalize()} Tıklanma Sayısı"
            # Kaydedilecek dosya adını oluştur
            fig_name = f"{period}_clicks"
            # Grafiği çiz ve kaydet
            plot_graph(period_df, period, title, fig_name)
        else:
            # Eğer veri yoksa, konsola bilgi mesajı yazdır
            print(f"No data available for {period} graph")
    
    # Çalışma dizinini eski haline getir
    os.chdir(old_dir)
