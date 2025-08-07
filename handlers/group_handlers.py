"""
Grup Handler'ları
Bu dosya grup mesajlarını ve yasaklı kelimeleri yönetir.
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from config import Config
from services.group_service import GroupService

router = Router()

@router.message(F.chat.type == ChatType.SUPERGROUP)
async def handle_group_message(message: Message):
    """Grup mesajlarını işler"""
    # Bot mesajlarını yoksay
    if message.from_user.is_bot:
        return
    
    # Yasaklı kelimeleri kontrol et
    group_service = GroupService(message.bot)
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

@router.message(F.chat.type == ChatType.GROUP)
async def handle_group_message_group(message: Message):
    """Normal grup mesajlarını işler"""
    # Bot mesajlarını yoksay
    if message.from_user.is_bot:
        return
    
    # Yasaklı kelimeleri kontrol et
    group_service = GroupService(message.bot)
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
