"""
Telegram Bot Ana Dosyası
Bu dosya botun giriş noktasıdır.
"""

import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import Config
from handlers.user_handlers import dp as user_dp
from handlers.admin_handlers import dp as admin_dp
from handlers.group_handlers import dp as group_dp
from services.database import DatabaseService
from services.storage_service import StorageService
from services.group_service import GroupService

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    """Bot komutlarını ayarlar (bot_settings varsa onu kullanır)."""
    # Varsayılan komutlar
    default_commands = [
        BotCommand(command="start", description="Botu başlat"),
        BotCommand(command="admin", description="Admin paneli"),
        BotCommand(command="help", description="Yardım"),
    ]

    try:
        db = DatabaseService()
        settings = await db.get_bot_settings()
        commands_json = settings.get('commands') if settings else None
        if commands_json:
            try:
                data = json.loads(commands_json)
                commands = []
                for item in data:
                    cmd = (item.get('command') or '').strip().lstrip('/')
                    desc = (item.get('description') or '').strip()
                    if cmd and desc:
                        commands.append(BotCommand(command=cmd, description=desc))
                if commands:
                    await bot.set_my_commands(commands)
                    logger.info("Bot komutları bot_settings'tan güncellendi (%d komut)", len(commands))
                    return
            except Exception as e:
                logger.warning("Komut JSON parse hatası: %s", e)
    except Exception as e:
        logger.warning("Bot ayarları okunamadı: %s", e)

    # Fallback varsayılanlar
    await bot.set_my_commands(default_commands)

async def on_startup(bot: Bot):
    """Bot başlatıldığında çalışır"""
    logger.info("Bot başlatılıyor...")
    
    # Konfigürasyonu doğrula
    try:
        Config.validate_config()
        logger.info("Konfigürasyon doğrulandı.")
    except ValueError as e:
        logger.error(f"Konfigürasyon hatası: {e}")
        return
    
    # Komutları ayarla
    await set_commands(bot)
    
    # Veritabanı bağlantısını test et
    try:
        db = DatabaseService()
        # Test sorgusu
        questions = await db.get_questions()
        logger.info(f"Veritabanı bağlantısı başarılı. {len(questions)} soru bulundu.")
    except Exception as e:
        logger.error(f"Veritabanı bağlantı hatası: {e}")
        return
    
    # Storage servisini başlat ve bucket'ı kontrol et
    try:
        storage = StorageService()
        await storage.ensure_bucket_exists()
        logger.info("Supabase Storage bağlantısı başarılı.")
    except Exception as e:
        logger.error(f"Storage bağlantı hatası: {e}")
        return
    
    logger.info("Bot başarıyla başlatıldı!")

async def on_shutdown(bot: Bot):
    """Bot kapatıldığında çalışır"""
    logger.info("Bot kapatılıyor...")

async def main():
    """Ana fonksiyon"""
    # Bot ve dispatcher oluştur
    bot = Bot(token=Config.BOT_TOKEN)
    
    # Storage seçimi (Redis varsa Redis, yoksa Memory)
    try:
        from aiogram.contrib.fsm_storage.redis import RedisStorage2
        storage = RedisStorage2(host='localhost', port=6379, db=0)
        logger.info("Redis storage kullanılıyor.")
    except ImportError:
        storage = MemoryStorage()
        logger.info("Memory storage kullanılıyor.")
    
    dp = Dispatcher(bot, storage=storage)
    
    # Handler'ları ekle
    user_dp(bot, dp)
    admin_dp(bot, dp)
    group_dp(bot, dp)
    
    # Bot'u başlat
    try:
        # Startup işlemlerini yap
        await on_startup(bot)
        
        await dp.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot durduruldu.")
    except Exception as e:
        logger.error(f"Bot çalışırken hata oluştu: {e}")
    finally:
        # Shutdown işlemlerini yap
        await on_shutdown(bot)
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
