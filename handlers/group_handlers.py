"""
Grup Handler'ları
Bu dosya grup mesajlarını ve yasaklı kelimeleri yönetir.
"""

from aiogram import Dispatcher, types

from config import Config
from services.group_service import GroupService

async def handle_group_message(message: types.Message):
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

async def handle_group_message_group(message: types.Message):
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

def dp(bot, dispatcher):
    """Dispatcher'a group handler'ları ekler"""
    # Supergroup ve group mesajları için handler'lar
    dispatcher.register_message_handler(handle_group_message, content_types=['text'], chat_type='supergroup')
    dispatcher.register_message_handler(handle_group_message_group, content_types=['text'], chat_type='group')
