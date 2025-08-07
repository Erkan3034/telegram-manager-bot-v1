from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    """Application runtime settings loaded from environment.

    Note: Keep secrets in your local .env file, never commit real tokens.
    """

    bot_token: str
    admin_ids: List[int]
    main_group_id: int
    shopier_payment_url: str

    supabase_url: str
    supabase_key: str
    supabase_bucket_receipts: str = "receipts"

    # Moderation
    banned_words: List[str] = None  # populated below

    @staticmethod
    def from_env() -> "Settings":
        bot_token = os.getenv("BOT_TOKEN", "")
        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required. Put it in your .env file.")

        admin_ids_raw = os.getenv("ADMIN_IDS", "")
        if not admin_ids_raw:
            raise RuntimeError("ADMIN_IDS is required. Example: ADMIN_IDS=123456789,987654321")

        admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]

        main_group_id_raw = os.getenv("MAIN_GROUP_ID", "")
        if not main_group_id_raw:
            raise RuntimeError("MAIN_GROUP_ID is required.")

        shopier_payment_url = os.getenv("SHOPIER_PAYMENT_URL", "https://shopier.com/orneksatis")

        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not supabase_url or not supabase_key:
            raise RuntimeError("Supabase credentials are required: SUPABASE_URL and SUPABASE_ANON_KEY (or SERVICE key).")

        banned_words_raw = os.getenv(
            "BANNED_WORDS",
            "küfür,aptal,salak,mal,piç,orospu,ibne,gerizekalı,lanet"  # sample defaults
        )
        banned_words = [w.strip().lower() for w in banned_words_raw.split(",") if w.strip()]

        return Settings(
            bot_token=bot_token,
            admin_ids=admin_ids,
            main_group_id=int(main_group_id_raw),
            shopier_payment_url=shopier_payment_url,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            banned_words=banned_words,
        )


settings = Settings.from_env()


