# Proje Adı

Bu proje, [proje adı] olarak adlandırılmıştır ve [proje amacı veya açıklaması] için geliştirilmiştir.

## Ne İşe Yarar?

Bu proje, GitHub üzerindeki Camo kullanan repoların tıklanma verilerini toplar ve bu verileri Google Sheets'e yazar. Bu sayede, kullanıcılar tıklanma verilerini daha sonra analiz edebilir ve projelerinin popülerliğini veya erişimini değerlendirebilirler.

## Nasıl Çalıştırılır?

Projenin çalıştırılması için aşağıdaki adımları izleyin:

1. **Gereksinimler**: Projeyi çalıştırmak için aşağıdaki yazılımların yüklü olduğundan emin olun:
   - Python >= 3.9
   - Gerekli Python kütüphaneleri (`requests`, `beautifulsoup4`, `google-api-python-client`, `google-auth`, `oauthlib`, `gspread`)

2. **Kurulum**:
   - Proje dosyalarını bilgisayarınıza indirin veya klonlayın.
   - Paket çakışması olmaması adına `venv` kullanmanız önerilir. 
   - Gerekli Python kütüphanelerini yüklemek için terminalde aşağıdaki komutu çalıştırın:
     ```
     pip3 install -r requirements.txt
     ```

3. **Çalıştırma**:
   - Projeyi çalıştırmak için terminalde aşağıdaki komutu kullanın:
     ```
     python3 main.py
     ```

## Config Dosyası

Proje, yapılandırma ayarlarını `config.json` dosyasından alır. Bu dosya, aşağıdaki gibi yapılandırılmıştır:

```json
{
  "spreadsheet_name": "Örnek Tablo",
  "interval_seconds": 60,
  "camo_url": "https://komarev.com/ghpvc/?username=xxx",
  "writer_emails": ["example@example.com"]
}
```

- **spreadsheet_name**: Kullanacağınız Google Sheet'in adını belirtir. Bu, verilerin kaydedileceği tabloyu tanımlar. Örneğin, "Proje Verileri" gibi bir ad kullanabilirsiniz.
- **interval_seconds**: Kaç saniyede bir tıklanma verisinin kaydedileceğini belirler. Örneğin, 60 değeri, her 60 saniyede bir verilerin güncellenmesini sağlar. Bu, veri toplama sıklığını ayarlamak için kullanılır.
- **camo_url**: İzlenecek GitHub reposunun tıklanma sayısının bulunduğu URL'yi belirtir. Bu URL, Camo kullanan repoların tıklanma verilerini çekmek için kullanılır.
- **writer_emails**: Google Sheet'e yazma izni vermek istediğiniz kişilerin e-posta adreslerini içerir. Bu, verilerin kaydedileceği tabloya kimlerin erişim izni olduğunu belirler. Birden fazla e-posta adresi ekleyebilirsiniz.

Bu dosya, projenin çalışması için gerekli olan tüm yapılandırma ayarlarını içerir. Herhangi bir değişiklik yapmanız gerektiğinde, bu dosyayı düzenleyebilirsiniz. Bu yapılandırma, projenizin doğru ve etkili bir şekilde çalışmasını sağlamak için önemlidir.