# Git Hit Monitor

Bu proje, Camo'yu kullanan GitHub repolarını izleyip tıklanmalarını ileride analiz edilmek üzere Google Sheets'e yazmak için geliştirilmiştir.
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

## Credentials Dosyası
Projenin Google Sheets ile etkileşim kurabilmesi için bir `credentials.json` dosyasına ihtiyaç vardır. Bu dosya, Google API'lerine erişim sağlamak için gerekli kimlik bilgilerini içerir. Aşağıda, bu dosyanın nasıl alınacağına dair adımlar bulunmaktadır:
### Credentials Dosyası Nasıl Alınır?
1. **Google Cloud Console'a Giriş Yapın**: [Google Cloud Console](https://console.cloud.google.com/) adresine gidin ve Google hesabınızla giriş yapın.
1. **Yeni Proje Oluşturun**: Sol üst köşedeki proje seçici menüsünden "Yeni Proje" seçeneğini tıklayın ve projenizi oluşturun.
1. **API'leri Etkinleştirin**: Projenizi seçtikten sonra, "API'ler ve Hizmetler" menüsüne gidin ve "Kitaplık" seçeneğini tıklayın. Buradan "Google Sheets API" ve "Google Drive API" hizmetlerini etkinleştirin.
1. **Kimlik Bilgileri Oluşturun**: "API'ler ve Hizmetler" menüsünden "Kimlik Bilgileri" sekmesine gidin. "Kimlik Bilgileri Oluştur" butonuna tıklayın ve "Hizmet Hesabı" seçeneğini seçin.
1. **Hizmet Hesabı Detaylarını Girin**: Hizmet hesabı için bir ad ve açıklama girin.
1. **Anahtar Oluşturun**: Üst kısımdaki seçeneklerden `keys` seçeneğini seçip, `add key` butonuna tıkalyın. Tip olarak `json` tipini seçin.
1. **credentials.json Dosyasını Kaydedin**: İndirilen JSON dosyasını projenizin kök dizinine credentials.json adıyla kaydedin.
Bu adımlar, projenizin Google Sheets ile güvenli bir şekilde etkileşim kurabilmesi için gerekli olan kimlik bilgilerini sağlar. credentials.json dosyasını güvenli bir yerde sakladığınızdan emin olun ve başkalarıyla paylaşmaktan kaçının.