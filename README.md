# AWS IoT Core & ESP32 Tabanlı Çevresel Takip ve Otomatik Alarm Sistemi

Bu proje; ESP32 geliştirme kartı ve DHT11 sensörü kullanarak sıcaklık ve nem verilerini gerçek zamanlı olarak **AWS IoT Core** üzerine aktaran, eşik aşımlarında **AWS Lambda** ve **AWS SNS** üzerinden otomatik e-posta bildirimleri gönderen uçtan uca bir IoT çözümüdür.

## 🏗️ Sistem Mimarisi
`ESP32 (DHT11)` ➔ `AWS IoT Core (MQTT / TLS 1.2)` ➔ `AWS IoT Rule` ➔ `AWS Lambda` ➔ `Amazon SNS (E-Posta Uyarısı)`

## 🚀 Özellikler
- **Uç Cihaz (Edge):** ESP32 Dev Module
- **Sensör Entegrasyonu:** DHT11 Sıcaklık ve Nem Sensörü (GPIO 4)
- **Haberleşme Protokolü:** MQTT over TLS (Port 8883)
- **Güvenlik:** X.509 Karşılıklı Kimlik Doğrulama (Mutual Authentication)
- **Akıllı Eşik & Alarm:** Sıcaklık 30°C ve üzerine çıktığında telemetri verisine `Uyari` etiketi eklenir; AWS IoT Rule ve Lambda tetiklenerek Amazon SNS üzerinden yetkili e-posta adreslerine anlık alarm iletilir.

## 📦 Kurulum ve Çalıştırma
1. Bu repoyu bilgisayarınıza klonlayın veya indirin.
2. `secrets.example.h` dosyasının adını `secrets.h` olarak değiştirin.
3. Kendi Wi-Fi bilgilerinizi, AWS IoT Endpoint adresinizi ve AWS X.509 sertifika anahtarlarınızı `secrets.h` içine yerleştirin.
4. Gerekli kütüphaneleri (`DHT sensor library`, `MQTT`, `ArduinoJson`) Arduino IDE'ye kurun.
5. Kodu ESP32 kartınıza yükleyin.
