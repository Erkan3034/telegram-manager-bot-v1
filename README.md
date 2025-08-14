# Telegram Manager Bot

Bu proje, Instagram üzerinden gelen kullanıcıları karşılayan, tanıtım yapan, etkileşimli sorular soran, ödeme alan ve kullanıcıları özel Telegram gruplarına ekleyen kapsamlı bir Telegram botudur.

## 🚀 Özellikler

### Kullanıcı Özellikleri
- ✅ Hoş geldin mesajı ve tanıtım
- ✅ Etkileşimli soru-cevap sistemi
- ✅ Ödeme entegrasyonu (Shopier)
- ✅ Dekont yükleme sistemi
- ✅ Otomatik grup daveti

### Admin Özellikleri
- ✅ Admin paneli (`/admin` komutu)
- ✅ Soru yönetimi (ekleme/silme)
- ✅ Ödeme onaylama/reddetme
- ✅ Dekont onaylama/reddetme
- ✅ Grup üye yönetimi
- ✅ İstatistikler

### Grup Yönetimi
- ✅ Yasaklı kelime kontrolü
- ✅ Otomatik uyarı sistemi
- ✅ Admin bildirimleri
- ✅ Kullanıcı çıkarma yetkisi

## 📁 Proje Yapısı

```
telegram-manager-bot/
├── main.py                 # Ana bot dosyası
├── app.py                  # Flask web uygulaması
├── config.py              # Konfigürasyon dosyası
├── requirements.txt       # Python bağımlılıkları
├── env.example           # Örnek environment dosyası
├── README.md             # Bu dosya
├── handlers/             # Handler dosyaları
│   ├── user_handlers.py  # Kullanıcı handler'ları
│   ├── admin_handlers.py # Admin handler'ları
│   └── group_handlers.py # Grup handler'ları
├── services/             # Servis dosyaları
│   ├── database.py       # Supabase veritabanı servisi
│   ├── storage_service.py # Supabase Storage servisi
│   └── group_service.py  # Grup yönetimi servisi
├── templates/            # Flask template'leri
│   ├── index.html        # Ana sayfa
│   └── admin.html        # Admin paneli
├── static/              # Statik dosyalar
│   ├── css/             # CSS dosyaları
│   └── js/              # JavaScript dosyaları
# Artık Supabase Storage kullanılıyor - dosyalar cloud'da saklanıyor
```

## 🛠️ Kurulum

### 1. Gereksinimler

- Python 3.8+
- Supabase hesabı
- Telegram Bot Token
- Redis (opsiyonel)

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Environment Dosyası

`env.example` dosyasını kopyalayıp `.env` olarak yeniden adlandırın ve gerekli bilgileri doldurun:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
GROUP_ID=-1001234567890

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Payment Configuration
SHOPIER_PAYMENT_URL=https://www.shopier.com/payment/example
```

### 4. Supabase Kurulumu

#### Veritabanı Tabloları
Supabase'de aşağıdaki tabloları oluşturun:

#### Storage Bucket
Supabase Storage'da `receipts` adında public bir bucket oluşturun:

1. Supabase Dashboard → Storage → New Bucket
2. Bucket name: `receipts`
3. Public bucket: ✅ (işaretleyin)
4. File size limit: 10MB
5. Allowed MIME types: image/*, application/pdf

#### Users Tablosu
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);
```

#### Questions Tablosu
```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Answers Tablosu
```sql
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    question_id INTEGER REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Payments Tablosu
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount DECIMAL(10,2) DEFAULT 99.99,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Receipts Tablosu
```sql
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    file_url TEXT NOT NULL,
    file_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Group Members Tablosu
```sql
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    group_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);
```

### 5. Bot'u Başlat

```bash
python main.py
```

### 6. Web Uygulamasını Başlat

```bash
python app.py
```

## 🔧 Kullanım

### Bot Komutları

- `/start` - Botu başlat
- `/admin` - Admin paneli (sadece admin'ler)
- `/help` - Yardım

### Admin Panel Özellikleri

1. **Soruları Yönet**
   - Yeni soru ekle
   - Mevcut soruları sil

2. **Ödeme Yapanlar**
   - Bekleyen ödemeleri görüntüle
   - Ödemeleri onayla/reddet
   - Dekontları onayla/reddet

3. **Üyeler**
   - Grup üyelerini görüntüle
   - Üyeleri gruptan çıkar

4. **İstatistikler**
   - Toplam kullanıcı sayısı
   - Toplam ödeme sayısı
   - Bekleyen ödeme sayısı
   - Grup üye sayısı

## 🔒 Güvenlik

- Admin ID'leri environment dosyasında saklanır
- Yasaklı kelimeler otomatik kontrol edilir
- Dosya yükleme güvenliği (boyut ve tür kontrolü)
- Supabase RLS (Row Level Security) kullanımı önerilir

## 📝 Notlar

### Bot İzinleri

Bot'un grup yöneticisi olarak eklenmesi gereken izinler:
- ✅ Mesaj gönderme
- ✅ Mesaj silme
- ✅ Kullanıcıları davet etme
- ✅ Kullanıcıları çıkarma
- ✅ Davet linki oluşturma

### Dosya Yükleme

Desteklenen dosya türleri:
- PDF (.pdf)
- Resim (.jpg, .jpeg, .png)

Maksimum dosya boyutu: 10MB

## 🐛 Sorun Giderme

### Yaygın Sorunlar

1. **Bot token hatası**
   - `.env` dosyasındaki `BOT_TOKEN` değerini kontrol edin

2. **Supabase bağlantı hatası**
   - `SUPABASE_URL` ve `SUPABASE_KEY` değerlerini kontrol edin
   - Supabase projesinin aktif olduğundan emin olun

3. **Grup ID hatası**
   - Grup ID'sinin doğru olduğundan emin olun
   - Bot'un grupta olduğunu kontrol edin

4. **Dosya yükleme hatası**
   - `uploads` klasörünün yazma izni olduğundan emin olun
   - Dosya boyutunu kontrol edin

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add some amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

Sorularınız için issue açabilir veya iletişime geçebilirsiniz.
