import pandas as pd
import os
import sys

# Proje kök dizinini path'in başına ekle (site-packages çakışmasını önlemek için)
sys.path.insert(0, os.getcwd())
try:
    import helpers
    # Reload local helpers because it might have been loaded from site-packages
    import importlib
    importlib.reload(helpers)
except ImportError:
    pass

from helpers.plot_helper import plot_all_graphs
from helpers.enum_helper import AveragePeriodType

def create_dummy_data():
    # 2 yıllık saatlik veri oluştur
    dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='h')
    
    # Basit bir desen oluştur:
    # - Gündüz artan, gece azalan
    # - Hafta sonu daha az
    # - Yazın daha çok
    
    import numpy as np
    
    count = len(dates)
    # create positive base trend
    base_trend = np.linspace(1000, 50000, count) 
    
    # Saatlik döngü (Sinüs dalgası: öğlen zirve)
    daily_pattern = np.sin((dates.hour - 6) * 2 * np.pi / 24) * 50
    
    # Haftalık döngü (Hafta sonu düşüş)
    weekly_pattern = np.where(dates.dayofweek >= 5, -200, 200)
    
    # Mevsimsel (Yazın artış)
    monthly_pattern = np.sin((dates.month - 1) * 2 * np.pi / 12) * 500
    
    # Random noise with seed
    np.random.seed(42)
    noise = np.random.normal(0, 50, count)
    
    # Calculate cumulative sum but ensure positive steps or just add to base trend
    # The previous logic was: base + cumsum(...)
    # If cumsum becomes very negative, it kills the base trend.
    # Let's just make 'numbers' directly correlated with trend + patterns to avoid "zero" issues
    # accumulated value = cumulative clicks
    
    # Let's simulate 'clicks per hour' effectively and then cumsum it to get 'total number'
    # logical flow: clicks_per_hour -> cumulative sum -> 'number' column
    
    hourly_clicks = 50 + daily_pattern + np.where(dates.dayofweek >= 5, -10, 10) + noise
    # Ensure no negative clicks
    hourly_clicks = np.maximum(hourly_clicks, 1)
    
    numbers = 1000 + np.cumsum(hourly_clicks)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'number': numbers
    })
    return df

def main():
    print("Dummy veri oluşturuluyor...")
    df = create_dummy_data()
    print(f"{len(df)} satır veri oluşturuldu.")
    
    print("\nGrafikler çiziliyor...")
    # 'test_plots' klasörüne kaydet
    plot_all_graphs(df, plot_dir='test_plots', generate_range_plots=False)
    

    print("\nİşlem tamamlandı. 'test_plots/ortalama' klasörünü kontrol edin.")
    
    # Kontrol
    avg_dir = 'test_plots/ortalama'
    if os.path.exists(avg_dir):
        files = os.listdir(avg_dir)
        print(f"\nOluşturulan dosyalar ({len(files)}):")
        for f in sorted(files):
            print(f"- {f}")
            
        expected_files = [str(t.display_name) + ".svg" for t in AveragePeriodType]
        missing = [f for f in expected_files if f not in files]
        
        if missing:
            print(f"\nEksik dosyalar: {missing}")
        else:
            print("\nTüm beklenen dosyalar mevcut.")
    else:
        print(f"\nKlasör bulunamadı: {avg_dir}")

if __name__ == "__main__":
    main()
