Amaç
-----

Bu belge projenin mimari ilkelerini ve iyileştirme önerilerini özetler. Kod tabanının sürdürülebilir, test edilebilir ve genişletilebilir olması için kesinlikle SOLID prensiplerine uyulmalıdır ve uygun yerlerde tasarım kalıpları (design patterns) kullanılmalıdır.

Kilit Noktalar ve Öneriler
-------------------------
- **SOLID Uyma Zorunluluğu:** Kod, tek sorumluluk (SRP), açık/kapalı (OCP), Liskov yerine getirme (LSP), arayüz ayrımı (ISP) ve bağımlılıkların tersine çevrilmesi (DIP) prensiplerine göre düzenlenmelidir.
- **Design Patterns Kullanımı:** Karmaşık veya tekrar eden sorumluluklar için uygun desenler tercih edin (ör: `Strategy`, `Factory`, `Adapter`, `Repository`, `Observer`, `Template Method`, `Dependency Injection`). Desenler sadece ihtiyaç varsa ve getirileri netse kullanılmalı.
- **Sorumluluk Ayrımı:** `helpers` içindeki modüller tek bir göreve odaklanmalı; veri okuma, işleme, gösterim ve dışa yazma ayrı katmanlarda tutulmalı.
- **Bağımlılık Enjeksiyonu:** Global konfigürasyon/bağımlılıklar doğrudan modüllerde import edilmek yerine fonksiyon/nesne constructor'ları aracılığıyla enjekte edilmeli. Bu test edilebilirliği artırır.
- **Arayüz/Abstract Kullanımı:** İşlevselliğin sınırları için Python `abc` veya protokoller kullanarak açık sözleşmeler (interfaces) tanımlayın. Böylece farklı implementasyonlar kolayca değiştirilebilir.
- **Küçük, Test Edilebilir Birimler:** Her fonksiyon/metod küçük ve tek bir işi yapacak şekilde refactor edilmeli; birim testleri bu küçük birimler için yazılmalı.
- **Tip İpuçları ve Dokümantasyon:** Statik analize yardımcı olacak şekilde `typing` kullanımı ve kısa docstring'ler zorunlu olmalı.
- **Hatalar ve Edge Case'ler:** Girdi doğrulama ve anlamlı hata mesajları ekleyin; dış servis çağrıları için retry/circuit-breaker stratejileri düşünün.

Somut Öneriler (başlangıç için)
--------------------------------
- `process_data_helper.py`: Büyük bir dosya; burada `Strategy` (farklı periyot hesaplama stratejileri) ve küçük yardımcı sınıflar/işlevlere bölünme uygun. I/O (`sheet.get_all_values`) ve veri işleme ayrılmalı.
- `main.py`: Uygulama giriş noktası sadece orkestrasyon yapsın; konfigürasyon yükleme, servislere bağlanma ve gerekirse DI container/ön yapılandırma kullanılsın.
- `helpers` modülleri: Her biri için açık sorumluluk, ortak util kodları için ayrı util modülü ve test kapsamı genişletilsin.

Sonraki Adımlar
---------------
- Küçük bir refactor dalı açın; önce `process_data_helper.py`'yi SRP'ye göre bölün.
- Birkaç kritik birim testi yazın (örn. dönem hesaplama, boundary payı hesaplama).
- CI’ye lint (flake8/ruff) ve tip kontrol (`mypy`) ekleyin.
