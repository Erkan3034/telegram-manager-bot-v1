# 🚀 Telegram Manager Bot - Ücretsiz Deployment Rehberi

Bu rehber, Telegram Manager Bot'unu ücretsiz olarak yayına almanızı sağlar.

## 📋 Gereksinimler

- GitHub hesabı
- Telegram Bot Token (BotFather'dan)
- Supabase hesabı (ücretsiz tier)

## 🎯 Deployment Seçenekleri

### Seçenek 1: Render (Önerilen - Ücretsiz)
### Seçenek 2: Railway (Ücretsiz tier)
### Seçenek 3: Heroku (Ücretsiz tier artık yok)

---

## 🚀 Render ile Deployment (Önerilen)

### Adım 1: GitHub'a Kod Yükleme

```bash
# Git repository'yi başlat
git init
git add .
git commit -m "Initial commit"

# GitHub'da yeni repository oluştur ve push yap
git remote add origin https://github.com/KULLANICI_ADIN/repo-adi.git
git branch -M main
git push -u origin main
```

### Adım 2: Render'da Servis Oluşturma

1. [Render.com](https://render.com)'a git
2. "New +" → "Web Service" seç
3. GitHub repository'yi bağla
4. Ayarları yap:

**Web Service Ayarları:**
- **Name:** `telegram-manager-bot`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Plan:** `Free`

**Environment Variables:**
```
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
GROUP_ID=your_group_id
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=production
```

### Adım 3: Worker Service Oluşturma

1. "New +" → "Background Worker"
2. Aynı repository'yi seç
3. Ayarları yap:

**Worker Service Ayarları:**
- **Name:** `telegram-bot-worker`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`
- **Plan:** `Free`

**Environment Variables:** (Web service ile aynı)

---

## 🚂 Railway ile Deployment

### Adım 1: Railway'de Proje Oluşturma

1. [Railway.app](https://railway.app)'e git
2. "New Project" → "Deploy from GitHub repo"
3. Repository'yi seç

### Adım 2: Servisleri Yapılandırma

**Web Service:**
- **Service Type:** Web Service
- **Start Command:** `gunicorn app:app`
- **Port:** `5000`

**Worker Service:**
- **Service Type:** Background Worker
- **Start Command:** `python main.py`

**Environment Variables:** (Render ile aynı)

---

## 🔧 Environment Variables Açıklaması

| Değişken | Açıklama | Örnek |
|-----------|----------|-------|
| `BOT_TOKEN` | Telegram Bot Token | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_IDS` | Admin kullanıcı ID'leri | `123456789,987654321` |
| `GROUP_ID` | Telegram grup ID | `-1001234567890` |
| `SUPABASE_URL` | Supabase proje URL | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `FLASK_SECRET_KEY` | Flask secret key | `your-super-secret-key-here` |
| `FLASK_ENV` | Flask environment | `production` |

---

## 📱 Bot Kurulumu

### Adım 1: BotFather'dan Bot Oluşturma

1. Telegram'da [@BotFather](https://t.me/botfather)'a git
2. `/newbot` komutunu kullan
3. Bot adı ve username belirle
4. Token'ı kaydet

### Adım 2: Webhook Kurulumu (Opsiyonel)

```bash
# Webhook URL'ini ayarla
curl -F "url=https://your-app.onrender.com/webhook" \
     https://api.telegram.org/bot<BOT_TOKEN>/setWebhook
```

---

## 🧪 Test Etme

### Adım 1: Bot Testi

1. Telegram'da botunuza `/start` gönderin
2. Admin panelini test edin: `/admin`

### Adım 2: Web Panel Testi

1. Web panel URL'ine gidin: `https://your-app.onrender.com`
2. Admin girişi yapın
3. Tüm özellikleri test edin

---

## 🔍 Sorun Giderme

### Bot Çalışmıyor
- Environment variables'ları kontrol edin
- Log'ları inceleyin
- Bot token'ı doğrulayın

### Web Panel Açılmıyor
- Port ayarlarını kontrol edin
- Build log'larını inceleyin
- Requirements.txt'yi kontrol edin

### Database Bağlantı Hatası
- Supabase credentials'ları kontrol edin
- Network erişimini kontrol edin
- Database tablolarını kontrol edin

---

## 📊 Monitoring

### Render Dashboard
- Log'ları görüntüle
- Performance metrics'i takip et
- Error'ları izle

### Telegram Bot Logs
- Bot mesajlarını takip et
- User interactions'ları izle
- Error'ları logla

---

## 🎉 Başarı!

Bot'unuz artık yayında! 🚀

**Sonraki Adımlar:**
1. Bot'u test edin
2. Admin panelini kullanın
3. Kullanıcıları gruba davet edin
4. Ödemeleri yönetin

**Destek:**
- GitHub Issues
- Telegram Support Group
- Documentation

---

## 📝 Notlar

- **Free tier limitleri:** Aylık kullanım sınırları var
- **Auto-sleep:** Render free tier'da 15 dakika inaktif sonrası uyku modu
- **Database:** Supabase free tier'da 500MB limit
- **Backup:** Düzenli backup alın

**Happy Deploying! 🚀**
