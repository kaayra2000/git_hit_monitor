import pandas as pd
import matplotlib.pyplot as plt
import os
from . import process_data_helper

def plot_daily_graph(df: pd.DataFrame, title: str, fig_name: str = 'daily_clicks.png') -> None:
    """
    Günlük tıklanma sayılarını gösteren bir çizgi grafiği oluşturur ve kaydeder.

    Args:
        df (pd.DataFrame): Günlük tıklanma sayılarını içeren DataFrame.
        title (str): Grafik başlığı.
        fig_name (str, optional): Kaydedilecek grafik dosyasının adı. Varsayılan değer 'daily_clicks.png'.

    Returns:
        None

    """
    # DataFrame'den günlük tıklanma sayılarını çizdir
    df.plot(y='daily_clicks', figsize=(10, 5), title=title)
    
    # X ekseni etiketini ayarla
    plt.xlabel('Tarih')
    
    # Y ekseni etiketini ayarla
    plt.ylabel('Tıklanma Sayısı')
    
    # X ekseni tarihlerini 45 derece döndür
    plt.xticks(rotation=45)
    
    # Grafiğe ızgara ekle
    plt.grid()
    
    # Grafiğin düzenini optimize et
    plt.tight_layout()
    # Grafiği belirtilen dosya adıyla kaydet
    plt.savefig(fig_name)

def plot_all_graphs(df: pd.DataFrame, plot_dir: str = 'plots') -> None:
    """
    Verilen DataFrame'den tüm grafikleri oluşturur ve belirtilen dizine kaydeder.

    Args:
        df (pd.DataFrame): İşlenecek ve grafiği çizilecek veriyi içeren DataFrame.
        plot_dir (str, optional): Grafiklerin kaydedileceği dizin. Varsayılan değer 'plots'.

    Returns:
        None

    """
    # Eğer belirtilen dizin yoksa, oluştur
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    
    # Mevcut çalışma dizinini kaydet
    old_dir = os.getcwd()
    
    # Grafiklerin kaydedileceği dizine geç
    os.chdir(plot_dir)
    
    # Günlük tıklanma sayılarını hesapla
    daily_df = process_data_helper.calculate_daily_clicks(df)
    
    # Günlük tıklanma grafiğini çiz
    plot_daily_graph(daily_df, 'Günlük Tıklanma Sayısı')
    
    # Orijinal çalışma dizinine geri dön
    os.chdir(old_dir)
