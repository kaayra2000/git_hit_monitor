
import pandas as pd
import os
import shutil
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helpers.plot_helper import plot_all_graphs

def create_sample_data():
    # Create data spanning multiple years and months
    dates = pd.date_range(start='2024-01-01', end='2025-02-01', freq='h')
    # Simple data: click count = hour of day (to have predictable averages)
    data = {'timestamp': dates, 'number': [d.hour for d in dates]} 
    # Determine the cumulative number
    # This might be tricky because the system expects 'number' to be cumulative total?
    # process_data_helper.read_and_preprocess_data sorts by timestamp.
    # calculate_period_clicks takes differences.
    # But calculate_average_statistics takes 'df' and calls process_data_helper.calculate_period_clicks internally via AveragePeriodType.calculate_clicks
    # Wait, AveragePeriodType.GUNUN_SAATLERI source is SAATLIK.
    # SAATLIK calculates hourly differences.
    
    # If I want 10 clicks per hour:
    # 00:00 -> 0
    # 01:00 -> 10
    # 02:00 -> 20
    # ...
    
    cumulative_numbers = [i * 10 for i in range(len(dates))]
    df = pd.DataFrame({'timestamp': dates, 'number': cumulative_numbers})
    return df

def verify_plots():
    plot_dir = 'test_plots_output'
    if os.path.exists(plot_dir):
        shutil.rmtree(plot_dir)
    
    df = create_sample_data()
    
    print("Generating plots...")
    plot_all_graphs(df, plot_dir=plot_dir, generate_range_plots=True)
    
    # Verify directories and files
    expected_files = [
        'plots/ortalama/günün_saatleri/yillik/2024.svg',
        'plots/ortalama/günün_saatleri/yillik/2025.svg',
        'plots/ortalama/günün_saatleri/aylik/2024_01.svg',
        'plots/ortalama/günün_saatleri/aylik/2025_01.svg',
    ]
    
    missing_files = []
    for rel_path in expected_files:
        full_path = os.path.join(plot_dir, rel_path.replace('plots/', ''))
        if not os.path.exists(full_path):
            missing_files.append(rel_path)
            print(f"MISSING: {full_path}")
        else:
            print(f"FOUND: {full_path}")
            
    if missing_files:
        print(f"FAILED: Missing {len(missing_files)} files.")
        sys.exit(1)
    else:
        print("SUCCESS: All expected plots found.")
        
if __name__ == "__main__":
    verify_plots()
