from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from config import settings


class GroupService:
    """Telegram grup işlemleri için yardımcı sınıf.

    Botun ilgili grupta yönetici olduğundan emin olun. Aksi halde ekleme/çıkarma yetkileri çalışmaz.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def add_user_to_group(self, user_id: int) -> None:
        """Kullanıcıyı gruba davet linki ile yönlendirir.

        Not: Botlar kullanıcıları doğrudan gruba ekleyemez. Bunun yerine davet linki gönderilir.
        """
        try:
            invite = await self.bot.create_chat_invite_link(chat_id=settings.main_group_id, name="Ödeme Onay Daveti")
            await self.bot.send_message(chat_id=user_id, text=f"Ödemeniz onaylandı. Gruba katılmak için linke tıklayın: {invite.invite_link}")
        except TelegramBadRequest:
            pass

    async def kick_user(self, user_id: int) -> None:
        try:
            await self.bot.ban_chat_member(chat_id=settings.main_group_id, user_id=user_id)
            await self.bot.unban_chat_member(chat_id=settings.main_group_id, user_id=user_id)
        except TelegramBadRequest:
            pass


