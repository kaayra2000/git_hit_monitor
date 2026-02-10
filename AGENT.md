# Proje Amacı ve Tanımı
Projenin temel amacı, Git üzerindeki tıklanma (hit) sayılarını takip etmek, bu verileri Google Sheets üzerinden okumak ve çeşitli zaman aralıklarında (günlük, aylık, çeyreklik, yıllık) anlamlı görselleştirmeler (grafikler) oluşturmaktır. Proje, verileri "process" edip "plot" ederek kullanıcıya sunar.

# Yazılım Geliştirme Prensipleri (ZORUNLU)
Bu projede kod yazarken aşağıdaki prensiplere **kesinlikle** uyulmalıdır. Temiz, sade ve sürdürülebilir kod esastır.

## 1. Temel Prensipler
- **KISS (Keep It Simple, Stupid):** Çözümleri mümkün olduğunca basit tutun. Karmaşık yapılar yerine okunabilir ve anlaşılır kod yazın. Gereksiz optimizasyondan kaçının.
- **DRY (Don't Repeat Yourself):** Kod tekrarından kaçının. Ortak mantıkları yardımcı fonksiyonlara veya sınıflara taşıyın (Örn: `calculate_period_clicks` ve `GraphPlotter`).
- **SOLID Prensipleri:**
    - **S (Single Responsibility):** Her sınıf ve fonksiyonun tek bir sorumluluğu olmalı. (Örn: `process_data_helper` veri işler, `plot_helper` çizer).
    - **O (Open/Closed):** Kod gelişime açık, değişime kapalı olmalı. Yeni bir grafik türü eklemek için mevcut kodu değiştirmek yerine yeni bir sınıf türetilmelidir (`GraphPlotter` hiyerarşisi gibi).
    - **L (Liskov Substitution):** Alt sınıflar, üst sınıfların yerine geçebilmelidir.
    - **I (Interface Segregation):** İstemciler kullanmadıkları arayüzlere bağımlı olmamalıdır.
    - **D (Dependency Inversion):** Yüksek seviyeli modüller, düşük seviyeli modüllere doğrudan bağımlı olmamalı, soyutlamalara dayanmalıdır.

## 2. Tasarım Kalıpları (Design Patterns)
Projede uygun yerlerde tasarım kalıpları kullanılmalıdır. Mevcut kullanımlar ve öneriler:
- **Strategy Pattern:** Farklı hesaplama veya işlem stratejileri için (Örn: `_estimate_from_overall_trend` vs. `_calculate_boundary_share`).
- **Factory Pattern:** Nesne üretimini soyutlamak için (Örn: `GraphFactory`).
- **Template Method:** Ortak akışın ana sınıfta tanımlanıp, detayların alt sınıflarda uygulandığı durumlar için (Örn: `GraphPlotter.plot` metodunun iskeleti).

## 3. Kod Kalitesi ve Standartlar
- **Temiz Kod:** Değişken ve fonksiyon isimleri açıklayıcı olmalı. Yorum satırları "ne" yapıldığını değil, "neden" yapıldığını açıklamalı.
- **Tip İpuçları (Type Hinting):** Tüm fonksiyon ve metodlarda parametre ve dönüş tipleri belirtilmelidir (`typing`).
- **Dokümantasyon (Docstrings):** Modül, sınıf ve fonksiyonların başında kısa ve öz docstringler bulunmalıdır.
- **Hata Yönetimi:** Hatalar sessizce geçiştirilmemeli, anlamlı loglar veya kullanıcı bildirimleri ile yönetilmelidir.

# Proje Analizi ve Yapı
- **`main.py`**: Uygulamanın giriş noktasıdır. Konfigürasyonu yükler ve ana döngüyü (veri okuma -> işleme -> bekleme) yönetir. Orkestrasyon sorumluluğundadır.
- **`helpers/`**: İş mantığını barındıran modüller.
    - **`process_data_helper.py`**: Ham veriyi işler, periyotlara böler ve tıklama sayılarını hesaplar. Matematiksel mantık buradadır.
    - **`plot_helper.py`**: İşlenmiş veriyi görselleştirir. `GraphPlotter` sınıfı ve türevlerini içerir.
    - **`sheets_helper.py`**: Google Sheets API ile iletişimi sağlar.
    - **`enum_helper.py`**: Sabitler ve Enum yapıları (Periyot tipleri vb.) buradadır.
- **`plots/`**: Üretilen grafiklerin kaydedildiği dizindir.

**Geliştirme Yaparken:**
Yeni bir özellik eklerken önce "Bu kod nereye ait?" diye sorun. UI ile ilgiliyse UI dosyalarına, veri işleme ise helper'lara, görselleştirme ise plot modüllerine ekleyin. Her zaman mevcut mimariyi koruyun ve iyileştirin.
