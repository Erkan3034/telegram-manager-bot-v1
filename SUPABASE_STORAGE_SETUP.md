# Supabase Storage Kurulum Rehberi

Bu rehber, Telegram Manager Bot'un Supabase Storage entegrasyonunu kurmak için gerekli adımları açıklar.

##  Ön Gereksinimler

1. **Supabase Projesi**: Aktif bir Supabase projesi
2. **Supabase URL**: `https://<project-id>.supabase.co` formatında
3. **Supabase Anon Key**: Public anonim anahtar
4. **Python 3.10+**: Bot için gerekli Python sürümü

## 📋 Adım 1: Supabase Dashboard'da Storage Bucket Oluşturma

### 1.1 Supabase Dashboard'a Giriş
- [Supabase Dashboard](https://app.supabase.com) adresine gidin
- Projenizi seçin

### 1.2 Storage Bucket Oluşturma
1. Sol menüden **Storage** seçin
2. **New Bucket** butonuna tıklayın
3. Aşağıdaki ayarları yapın:
   - **Name**: `receipts`
   - **Public bucket**: ✅ (işaretleyin)
   - **File size limit**: `10MB`
   - **Allowed MIME types**: `image/*, application/pdf`

### 1.3 Bucket Ayarlarını Kontrol Etme
- Bucket oluşturulduktan sonra **Settings** sekmesine gidin
- **Public bucket** seçeneğinin aktif olduğundan emin olun
- **Policies** sekmesinde public erişim izinlerini kontrol edin

## 📋 Adım 2: Environment Değişkenlerini Ayarlama

### 2.1 .env Dosyası Oluşturma
Proje ana dizininde `.env` dosyası oluşturun:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
GROUP_ID=-1001234567890

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Payment Configuration
SHOPIER_PAYMENT_URL=https://www.shopier.com/payment/example
```

### 2.2 Supabase Bilgilerini Alma
1. **Project Settings** → **API** sekmesine gidin
2. **Project URL**'yi kopyalayın → `SUPABASE_URL`
3. **anon public** key'i kopyalayın → `SUPABASE_KEY`

## 📋 Adım 3: Veritabanı Tablolarını Oluşturma

### 3.1 SQL Editor'da Tabloları Oluşturma
Supabase Dashboard → **SQL Editor** → **New Query**:

```sql
-- Users tablosu
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

-- Questions tablosu
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Answers tablosu
CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    question_id INTEGER REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payments tablosu
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    amount DECIMAL(10,2) DEFAULT 99.99,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Receipts tablosu
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    file_url TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Group members tablosu
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    group_id BIGINT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

-- Bot settings tablosu
CREATE TABLE bot_settings (
    id SERIAL PRIMARY KEY,
    start_message TEXT,
    help_message TEXT,
    intro_message TEXT,
    promotion_message TEXT,
    payment_message TEXT,
    commands JSONB,
    group_id BIGINT,
    shopier_payment_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages tablosu
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    order_index INTEGER DEFAULT 0,
    delay DECIMAL(3,1) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Admins tablosu
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 📋 Adım 4: Bot'u Test Etme

### 4.1 Bot'u Başlatma
```bash
python main.py
```

### 4.2 Test Mesajı Gönderme
1. Telegram'da bot'unuza `/start` komutu gönderin
2. Bot'un çalıştığını ve mesajları aldığını kontrol edin

### 4.3 Dekont Yükleme Testi
1. Bot size dekont yüklemenizi istediğinde
2. Bir fotoğraf veya PDF dosyası gönderin
3. Dosyanın Supabase Storage'a yüklendiğini kontrol edin

## 📋 Adım 5: Admin Paneli Testi

### 5.1 Web Uygulamasını Başlatma
```bash
python app.py
```

### 5.2 Admin Paneline Erişim
1. Tarayıcıda `http://localhost:5000/admin` adresine gidin
2. Admin bilgilerinizle giriş yapın
3. Dekontları ve dosya URL'lerini kontrol edin

## 🔧 Sorun Giderme

### Storage Bucket Hatası
```
❌ Receipts bucket bulunamadı
```
**Çözüm**: Supabase Dashboard → Storage → New Bucket → `receipts` adında public bucket oluşturun

### Dosya Yükleme Hatası
```
❌ Dosya yüklenemedi
```
**Çözüm**: 
1. Bucket'ın public olduğundan emin olun
2. Dosya boyutunun 10MB altında olduğunu kontrol edin
3. Dosya türünün desteklendiğini kontrol edin (JPG, PNG, PDF)

### Veritabanı Bağlantı Hatası
```
❌ Veritabanı bağlantı hatası
```
**Çözüm**:
1. `.env` dosyasındaki `SUPABASE_URL` ve `SUPABASE_KEY` değerlerini kontrol edin
2. Supabase projesinin aktif olduğundan emin olun
3. Anon key'in doğru olduğunu kontrol edin

## 📱 Mobil Uygulama Testi

### Telegram Bot Testi
1. Bot'u mobil Telegram uygulamasında test edin
2. Fotoğraf yükleme işlemini mobil cihazdan test edin
3. Dosya boyutu ve türü kısıtlamalarını kontrol edin

## 🚀 Production Deployment

### Heroku Deployment
1. `Procfile` dosyası zaten mevcut
2. Heroku'da environment variables'ları ayarlayın
3. `runtime.txt` dosyası Python 3.11.7 için ayarlanmış

### VPS Deployment
1. Gunicorn ile production server başlatın
2. Nginx reverse proxy kullanın
3. SSL sertifikası ekleyin

## 📊 Monitoring ve Logs

### Bot Logları
- Bot çalışırken console'da detaylı loglar görünür
- Hata durumlarında stack trace yazdırılır

### Storage Logları
- Supabase Dashboard → Storage → Logs
- Dosya yükleme/indirme işlemlerini takip edin

### Veritabanı Logları
- Supabase Dashboard → Database → Logs
- SQL sorgularını ve performansı takip edin

## 🎯 Son Kontroller

✅ Storage bucket `receipts` oluşturuldu ve public yapıldı  
✅ Veritabanı tabloları oluşturuldu  
✅ Environment variables ayarlandı  
✅ Bot başarıyla başlatıldı  
✅ Dekont yükleme testi başarılı  
✅ Admin panelinde dosya URL'leri görünüyor  
✅ Mobil cihazlarda test edildi  

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Console loglarını kontrol edin
2. Supabase Dashboard'da bucket ve tabloları kontrol edin
3. Environment variables'ları doğrulayın
4. Dosya boyutu ve türü kısıtlamalarını kontrol edin
