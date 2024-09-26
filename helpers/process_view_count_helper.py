
from .camo_helper import get_number_from_url
from .sheets_helper import append_to_sheet
from .plot_helper import plot_all_graphs
from .string_helper import convert_to_int

import typing
if typing.TYPE_CHECKING:
    import pandas as pd
def process_view_count(camo_url: str, sheet: object, df: 'pd.DataFrame', value_threshold: float) -> tuple['pd.DataFrame', int, int]:
    """
    Görüntülenme sayısını alır, işler ve çalışma sayfasına ekler.

    Args:
        camo_url (str): Görüntülenme sayısının alınacağı URL.
        sheet (object): Verilerin ekleneceği çalışma sayfası nesnesi.
        df (pd.DataFrame): Mevcut verileri içeren DataFrame.
        value_threshold (float): Değerleri karşılaştırmak için kullanılan eşik değeri.

    Returns:
        tuple[pd.DataFrame, int, int]: 
            - Güncellenmiş DataFrame
            - Eklenen satır sayısı (0 veya 1)
            - İşlenen görüntülenme sayısı (başarısız olursa 0)
    """
    view_count_str, is_successful = get_number_from_url(camo_url)
    if not is_successful:
        print(f"\n{view_count_str}")
        return df, 0, 0

    view_count = convert_to_int(view_count_str)
    is_successful, is_appended, append_date = append_to_sheet(sheet, view_count, value_threshold)
    df_tuple = [append_date, view_count]

    if is_successful:
        if is_appended:
            # Yeni bir satır eklendi
            df.loc[len(df)] = df_tuple
            append_counter = 1
        else:
            # Mevcut son satır güncellendi
            df.loc[len(df) - 1] = df_tuple
            append_counter = 0
        
        plot_all_graphs(df)
        return df, append_counter, view_count
    else:
        print("\nGörüntülenme sayısı eklenirken bir hata oluştu.")
        return df, 0, 0
