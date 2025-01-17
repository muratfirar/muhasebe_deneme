# Muhasebe Analiz Sistemi

## Versiyon 1.0

### Özellikler
- 3 döneme kadar XML veri girişi desteği
- Detaylı mizan raporu oluşturma
- Dönemler arası karşılaştırmalı analiz
- Muhasebe fişleri görüntüleme ve filtreleme
- Modern ve kullanıcı dostu arayüz

### Teknolojiler
- Python/Flask
- Tailwind CSS
- JavaScript

### Kurulum
1. Gereksinimleri yükleyin:

### Hata Ayıklama

1. Veritabanı bağlantı hatası durumunda:
   - PostgreSQL servisinin çalıştığından emin olun
   - Veritabanı kullanıcı ve şifresini kontrol edin
   - `test_db.py` ile bağlantıyı test edin

2. XML yükleme hataları için:
   - XML dosyasının doğru formatta olduğunu kontrol edin
   - `uploads` klasörünün yazma izinlerini kontrol edin

### Güvenlik Notları

- Hassas veritabanı bilgilerini güvenli bir şekilde saklayın
- Üretim ortamında `SECRET_KEY`'i değiştirin
- XML dosyalarının güvenliğini sağlayın

### Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

### İletişim

Sorularınız ve önerileriniz için:
- GitHub Issues
- [E-posta Adresi]

### Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Pull Request oluşturun