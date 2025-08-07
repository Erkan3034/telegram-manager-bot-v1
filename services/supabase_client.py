from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List, Optional

from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings


class SupabaseClient:
    """Supabase erişimi için yardımcı sınıf.

    Notlar:
    - supabase-py eşzamanlı çalışır, bot yükünüz çok yüksek değilse doğrudan çağrı uygundur.
    - Gerekirse ileride thread pool ile sarmalanabilir.
    """

    def __init__(self) -> None:
        self._client: Client = create_client(settings.supabase_url, settings.supabase_key)

    # Beklenen tablo şemaları (Supabase tarafında oluşturulmalı):
    # users(telegram_user_id: bigint pk, username: text, created_at: timestamp)
    # questions(id: uuid pk default, text: text, order_index: int)
    # answers(id: uuid pk default, telegram_user_id: bigint, question_id: uuid, answer_text: text, created_at: timestamp)
    # payments(telegram_user_id: bigint pk, status: text, receipt_url: text, updated_at: timestamp)
    # admin_states(admin_user_id: bigint pk, state: text)
    # user_states(telegram_user_id: bigint pk, current_order_index: int)
    # members(telegram_user_id: bigint pk, joined_at: timestamp)

    # ---------- Users ----------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def upsert_user(self, telegram_user_id: int, username: Optional[str]) -> None:
        data = {
            "telegram_user_id": telegram_user_id,
            "username": username,
            "created_at": dt.datetime.utcnow().isoformat(),
        }
        self._client.table("users").upsert(data, on_conflict="telegram_user_id").execute()

    # ---------- Questions ----------

    async def list_questions(self) -> List[Dict[str, Any]]:
        res = self._client.table("questions").select("*").order("order_index", desc=False).execute()
        return res.data or []

    async def add_question(self, text: str) -> None:
        next_index = self._calc_next_index()
        self._client.table("questions").insert({"id": str(uuid.uuid4()), "text": text, "order_index": next_index}).execute()

    def _calc_next_index(self) -> int:
        res = self._client.table("questions").select("order_index").order("order_index", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            return int(res.data[0]["order_index"]) + 1
        return 1

    async def delete_question(self, question_id: str) -> None:
        self._client.table("questions").delete().eq("id", question_id).execute()

    async def get_question_by_order(self, order_index: int) -> Optional[Dict[str, Any]]:
        res = self._client.table("questions").select("*").eq("order_index", order_index).limit(1).execute()
        if res.data:
            return res.data[0]
        return None

    async def get_first_question(self) -> Optional[Dict[str, Any]]:
        res = self._client.table("questions").select("*").order("order_index", desc=False).limit(1).execute()
        if res.data:
            return res.data[0]
        return None

    async def get_next_question_for_user(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        state = await self.get_user_state(telegram_user_id)
        if state is None:
            # start from first question
            return await self.get_first_question()
        else:
            next_order = int(state) + 1
            return await self.get_question_by_order(next_order)

    # ---------- Answers ----------

    async def record_answer(self, telegram_user_id: int, question_id: str, answer_text: str) -> None:
        self._client.table("answers").insert({
            "id": str(uuid.uuid4()),
            "telegram_user_id": telegram_user_id,
            "question_id": question_id,
            "answer_text": answer_text,
            "created_at": dt.datetime.utcnow().isoformat(),
        }).execute()

    # ---------- User question state ----------

    async def set_user_state(self, telegram_user_id: int, current_order_index: Optional[int]) -> None:
        if current_order_index is None:
            self._client.table("user_states").delete().eq("telegram_user_id", telegram_user_id).execute()
        else:
            self._client.table("user_states").upsert({
                "telegram_user_id": telegram_user_id,
                "current_order_index": int(current_order_index),
            }, on_conflict="telegram_user_id").execute()

    async def get_user_state(self, telegram_user_id: int) -> Optional[int]:
        res = self._client.table("user_states").select("current_order_index").eq("telegram_user_id", telegram_user_id).limit(1).execute()
        if res.data:
            return int(res.data[0]["current_order_index"]) if res.data[0].get("current_order_index") is not None else None
        return None

    # ---------- Payments ----------

    async def set_payment_status(self, telegram_user_id: int, status: str, receipt_url: Optional[str] = None) -> None:
        data: Dict[str, Any] = {
            "telegram_user_id": telegram_user_id,
            "status": status,
            "updated_at": dt.datetime.utcnow().isoformat(),
        }
        if receipt_url is not None:
            data["receipt_url"] = receipt_url
        self._client.table("payments").upsert(data, on_conflict="telegram_user_id").execute()

    async def list_pending_payments(self) -> List[Dict[str, Any]]:
        res = self._client.table("payments").select("*").eq("status", "pending").execute()
        return res.data or []

    # ---------- Admin ephemeral state ----------

    async def set_admin_state(self, admin_user_id: int, state: Optional[str]) -> None:
        if state is None:
            self._client.table("admin_states").delete().eq("admin_user_id", admin_user_id).execute()
        else:
            self._client.table("admin_states").upsert({
                "admin_user_id": admin_user_id,
                "state": state,
            }, on_conflict="admin_user_id").execute()

    async def get_admin_state(self, admin_user_id: int) -> Optional[str]:
        res = self._client.table("admin_states").select("state").eq("admin_user_id", admin_user_id).limit(1).execute()
        if res.data:
            return res.data[0].get("state")
        return None

    # ---------- Members ----------

    async def add_member(self, telegram_user_id: int) -> None:
        self._client.table("members").upsert({
            "telegram_user_id": telegram_user_id,
            "joined_at": dt.datetime.utcnow().isoformat(),
        }, on_conflict="telegram_user_id").execute()

    async def list_members(self) -> List[Dict[str, Any]]:
        res = self._client.table("members").select("*").execute()
        return res.data or []

    # ---------- Storage (Receipts) ----------

    async def upload_receipt(self, filename: str, content: bytes, content_type: str) -> str:
        storage = self._client.storage()
        # Bucket varsa hata fırlatabilir, önemsemiyoruz
        try:
            storage.create_bucket(settings.supabase_bucket_receipts, public=True)
        except Exception:
            pass

        key = f"{dt.datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4()}_{filename}"
        storage.from_(settings.supabase_bucket_receipts).upload(path=key, file=content, file_options={"content-type": content_type})
        # Public URL
        public_url = storage.from_(settings.supabase_bucket_receipts).get_public_url(key)
        if isinstance(public_url, dict) and "publicUrl" in public_url:
            return public_url["publicUrl"]
        return str(public_url)


