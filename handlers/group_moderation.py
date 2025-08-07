from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message

from config import settings


group_router = Router(name="group_router")


@group_router.message(F.chat.type.in_({"group", "supergroup"}) & F.text)
async def moderate_group_messages(message: Message):
    text = (message.text or "").lower()
    if any(bad in text for bad in settings.banned_words):
        try:
            await message.reply("Lütfen uygun bir dil kullanınız. Bu bir uyarıdır.")
        except Exception:
            pass
        # İstenirse admin'e bildirim gönderilebilir
        # for admin_id in settings.admin_ids:
        #     try:
        #         await message.bot.send_message(admin_id, f"Uyarı: {message.from_user.id} uygunsuz mesaj: {message.text}")
        #     except Exception:
        #         pass


