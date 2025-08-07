## Telegram Manager Bot (aiogram v3 + Supabase)

Production odaklı, modüler bir Telegram botu. Instagram üzerinden gelen kullanıcıları karşılar, tanıtım gösterir, admin tarafından yönetilebilir soruları toplar, ödeme/dosya (dekont) sürecini Supabase ile yönetir, onay sonrası kullanıcıyı gruba davet eder ve grupta temel moderasyon uygular.

### Kurulum

1. Python 3.11+ sürümü kurulu olmalı.
2. Bağımlılıklar:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` dosyası oluşturup `config.py` içindeki anahtarları doldurun (bkz: `.env.example`).
4. Supabase'te şu tabloları oluşturun (örnek şema açıklamaları `services/supabase_client.py` içinde): `users, questions, answers, payments, admin_states, user_states, members`. Ayrıca `receipts` isimli public bucket oluşturun.
5. Botunuzu hedef Telegram grubuna admin olarak ekleyin (yönetim yetkileri için şarttır).

### Çalıştırma

```bash
python main.py
```

### Admin Paneli

- `/admin` komutu sadece `ADMIN_IDS` içinde olan kullanıcılar içindir.
- "Soruları Yönet": Yeni soru ekleme/silme.
- "Ödeme Bekleyenler": Kullanıcı dekontlarını görme, onay/red.
- "Üyeler": Gruba eklenen kullanıcılar listesi.

### Notlar

- Botlar kullanıcıları doğrudan gruba ekleyemez; ödeme onayı sonrası davet linki DM olarak gönderilir.
- Shopier ödeme linki `.env` üzerinden verilir.
- Yasaklı kelimeler `.env` ile yapılandırılır.


