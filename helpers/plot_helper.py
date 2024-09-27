import pandas as pd
import matplotlib.pyplot as plt
import os
from abc import ABC, abstractmethod
from . import process_data_helper
import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator

class GraphPlotter(ABC):
    def __init__(self, df: pd.DataFrame, title: str, y_column: str, x_label: str) -> None:
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
    def plot(self, fig_name: str) -> None:
        fig, ax = plt.subplots(figsize=(12, 6))

        # İndeksin tipini kontrol et ve datetime tipine dönüştür
        if isinstance(self.df.index, pd.PeriodIndex):
            self.df.index = self.df.index.to_timestamp()
        elif not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)

        # İndeks değerlerini Matplotlib'in anlayacağı float tipine dönüştür
        date_numbers = mdates.date2num(self.df.index)

        if len(self.df) > 1:
            ax.plot(date_numbers, self.df[self.y_column], marker='o')
        else:
            ax.bar(date_numbers, self.df[self.y_column], width=20)  # width değerini periyoda göre ayarlayabilirsiniz

        # X ekseni formatını periyoda göre ayarla
        if self.x_label == 'Yıl':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.xticks(rotation=0)
            offset = 366  # Bir yıl için
        elif self.x_label == 'Ay':
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45, ha='right')
            offset = 31  # Bir ay için
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45, ha='right')
            offset = 1  # Bir gün için

        # X ekseni limitlerini ayarla
        ax.set_xlim(date_numbers.min() - offset, date_numbers.max() + offset)

        # FixedLocator kullanımı - tarihleri numaralara dönüştürdük
        ax.xaxis.set_major_locator(FixedLocator(date_numbers))

        # Otomatik tarih formatlamasını etkinleştir
        ax.xaxis_date()

        self._set_common_properties(ax)
        plt.tight_layout()
        plt.savefig(fig_name)
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
        super().__init__(df, title, 'yearly_clicks', 'Yıl')

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
    def create_plotter(period: str, df: pd.DataFrame, title: str) -> GraphPlotter:
        """
        Belirtilen periyoda göre uygun GraphPlotter nesnesini oluşturan fabrika metodu.

        Args:
            period (str): Grafik periyodu ('günlük', 'aylık', 'çeyreklik', 'yıllık')
            df (pd.DataFrame): Çizilecek veriyi içeren DataFrame
            title (str): Grafiğin başlığı

        Returns:
            GraphPlotter: Oluşturulan GraphPlotter nesnesi
        """
        plotters = {
            'günlük': lambda: LineGraphPlotter(df, title, 'daily_clicks', 'Tarih'),
            'aylık': lambda: LineGraphPlotter(df, title, 'monthly_clicks', 'Ay'),
            'çeyreklik': lambda: LineGraphPlotter(df, title, 'quarterly_clicks', 'Çeyrek'),
            'yıllık': lambda: YearlyGraphPlotter(df, title)
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
        'günlük': process_data_helper.calculate_daily_clicks,
        'aylık': process_data_helper.calculate_monthly_clicks,
        'çeyreklik': process_data_helper.calculate_quarterly_clicks,
        'yıllık': process_data_helper.calculate_yearly_clicks
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
            fig_name = f"{period}_clicks.png"
            # Grafiği çiz ve kaydet
            plot_graph(period_df, period, title, fig_name)
        else:
            # Eğer veri yoksa, konsola bilgi mesajı yazdır
            print(f"No data available for {period} graph")
    
    # Çalışma dizinini eski haline getir
    os.chdir(old_dir)
