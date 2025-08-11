"""
Telegram Bot Konfigürasyon Dosyası
Bu dosya bot için gerekli tüm ayarları içerir.
"""

import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    """Bot konfigürasyon sınıfı"""
    
    # Telegram Bot Ayarları
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    GROUP_ID = int(os.getenv('GROUP_ID', 0))
    
    # Supabase Ayarları
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Flask Ayarları
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Ödeme Ayarları
    SHOPIER_PAYMENT_URL = os.getenv('SHOPIER_PAYMENT_URL', 'https://www.shopier.com/payment/example')
    
    # Bot Ayarları
    WELCOME_MESSAGE = "Hoş geldin, {username}! 🎉\n\nKompass Network ailesine katılmak için hazır mısın?"
    INTRO_MESSAGE = """
🌟 **Kompass Network'e Hoş Geldiniz!**

Bu bot, özel içeriklerimizden yararlanmanız için tasarlanmıştır.
Aşağıdaki butona tıklayarak detaylı tanıtımımızı görebilirsiniz.
    """
    
    # Tanıtım Mesajı
    PROMOTION_MESSAGE = """
🚀 **Kompass Network Özel İçerik Paketi**

✨ **Neler Sunuyoruz:**
• 📚 Özel eğitim içerikleri
• 🎥 Canlı yayınlar
• 👥 Topluluk desteği
• ⭐ VIP erişim
• 🎯 Özel danışmanlık

💰 **Fiyat:** 99.99 TL

📋 Devam etmek için aşağıdaki soruları yanıtlayın.
Bu sorular sayesinde size daha iyi hizmet verebiliriz.
    """
    
    # Varsayılan Sorular
    DEFAULT_QUESTIONS = [
        "Adınız nedir?",
        "Soyadınız nedir?",
        "Neden katılmak istiyorsunuz?",
        "Telefon numaranız nedir?"
    ]
    
    # Yasaklı Kelimeler
    BANNED_WORDS = [
        "küfür", "hakaret", "kötü", "berbat", "rezalet",
        "aptal",  "ahmak","şerefsiz", "ahmak", "ibne", "aptal", "mal", "salak", "gerizekalı", "oç", "orospu", "piç", "şerefsiz",
    "haysiyetsiz", "karaktersiz", "adi", "sürtük", "p.ç", "kahpe", "yavşak", "godoş", "top",
    "pezevenk", "gavat", "it", "inek", "dingil", "embesil", "aptalca", "ezik", "yobaz",
    "puşt", "lanet", "şırfıntı", "züppe", "hayvan", "yamyam", "salakça", "sığır", "gerzek",
    "bunak", "yalaka", "serseri", "çomar", "domuz", "yavşakça", "bok", "b.k", "kaltak",
    "dangalak", "akılsız", "bağnaz", "soysuz", "manyak"
    ]
    
    # Dosya Yükleme Ayarları
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    @classmethod
    def validate_config(cls):
        """Konfigürasyon değerlerini doğrular"""
        required_fields = [
            'BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Eksik konfigürasyon değerleri: {', '.join(missing_fields)}")
        
        return True
