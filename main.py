from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import user_router, group_router
from admin_panel import admin_router
from services.supabase_client import SupabaseClient
from services.group_service import GroupService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    # Bot ve Dispatcher
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Services (simple DI)
    supa = SupabaseClient()
    groups = GroupService(bot)

    # Middlewares: supply services via context
    dp.update.outer_middleware(ServiceMiddleware(supa=supa, groups=groups))

    # Routers
    dp.include_routers(user_router, admin_router, group_router)

    # Start polling
    logging.info("Bot started. Make sure the bot is admin in your target group.")
    await dp.start_polling(bot)


class ServiceMiddleware:
    """Basit servis enjeksiyonu için middleware.

    Handler fonksiyonlarında parametre ismiyle (supa, groups) servislere erişim sağlanır.
    """

    def __init__(self, supa: SupabaseClient, groups: GroupService) -> None:
        self.supa = supa
        self.groups = groups

    async def __call__(self, handler, event, data):
        data["supa"] = self.supa
        data["groups"] = self.groups
        return await handler(event, data)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")


