"""
Grup Handler'ları
Bu dosya grup mesajlarını ve yasaklı kelimeleri yönetir.
aiogram 3.x uyumlu
"""

from aiogram import Router, types, F, Bot
from aiogram.enums import ChatType

from config import Config
from services.group_service import GroupService

# Router oluştur
router = Router()

@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), F.text)
async def handle_group_message(message: types.Message, bot: Bot):
    """Grup mesajlarını işler"""
    # Bot mesajlarını yoksay
    if message.from_user.is_bot:
        return
    
    # Yasaklı kelimeleri kontrol et
    group_service = GroupService(bot)
    has_banned_words = await group_service.handle_banned_message(
        message.from_user.id,
        message.text
    )
    
    if has_banned_words:
        # Mesajı sil (eğer bot yönetici ise)
        try:
            await message.delete()
        except:
            pass  # Bot yönetici değilse mesajı silemez
