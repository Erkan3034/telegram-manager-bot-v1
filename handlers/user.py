from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from services.supabase_client import SupabaseClient


user_router = Router(name="user_router")


def promo_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="Tanıtımı Gör", callback_data="promo:show")
    kb.adjust(1)
    return kb


def payment_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Ödeme Yaptım", callback_data="pay:done")
    kb.button(text="📎 Dekont Ekle", callback_data="pay:upload")
    kb.adjust(1)
    return kb


PROMO_TEXT = (
    "Hoş geldiniz! Bu özel grupta haftalık içerikler, kapanış stratejileri ve canlı oturumlar sizi bekliyor.\n\n"
    "Katılmak için hızlıca birkaç soruya cevap verin ve ardından ödeme adımına geçelim."
)


@user_router.message(CommandStart())
async def start(message: Message, supa: SupabaseClient):
    username = message.from_user.username if message.from_user else None
    user_id = message.from_user.id
    await supa.upsert_user(user_id, username)
    await supa.set_user_state(user_id, None)  # reset flow
    await message.answer(f"Hoş geldin, @{username or user_id}")
    await message.answer("Tanıtımı görmek için tıklayın:", reply_markup=promo_keyboard().as_markup())


@user_router.callback_query(F.data == "promo:show")
async def show_promo(callback: CallbackQuery, supa: SupabaseClient):
    await callback.message.answer(PROMO_TEXT)
    # İlk soruyu soralım
    q = await supa.get_first_question()
    if q:
        await supa.set_user_state(callback.from_user.id, int(q["order_index"]))
        await callback.message.answer(q["text"]) 
    else:
        # Soru yoksa direkt ödeme adımına geç
        await callback.message.answer(
            f"Ödeme için bağlantı: {settings.shopier_payment_url}",
            reply_markup=payment_keyboard().as_markup(),
        )
    await callback.answer()


@user_router.message(F.text & ~CommandStart())
async def collect_answers(message: Message, supa: SupabaseClient):
    user_id = message.from_user.id
    current_order = await supa.get_user_state(user_id)
    if current_order is None:
        return  # out of flow; ignore free-text

    # mevcut soruyu al
    q = await supa.get_question_by_order(current_order)
    if q:
        await supa.record_answer(user_id, q["id"], message.text)

    # sıradaki soruyu getir
    next_q = await supa.get_next_question_for_user(user_id)
    if next_q:
        await supa.set_user_state(user_id, int(next_q["order_index"]))
        await message.answer(next_q["text"])
    else:
        # sorular bitti -> ödeme adımı
        await supa.set_user_state(user_id, None)
        await message.answer(
            f"Teşekkürler! Şimdi ödeme adımına geçebilirsiniz. Bağlantı: {settings.shopier_payment_url}",
            reply_markup=payment_keyboard().as_markup(),
        )


@user_router.callback_query(F.data == "pay:upload")
async def prompt_receipt(callback: CallbackQuery):
    await callback.message.answer("Lütfen dekontu PDF, JPG veya PNG olarak gönderin.")
    await callback.answer()


@user_router.message(F.document | F.photo)
async def handle_receipt(message: Message, supa: SupabaseClient):
    # PDF veya resim desteği
    file_name = None
    file_bytes = None
    content_type = "application/octet-stream"

    if message.document:  # likely PDF or other file
        file_name = message.document.file_name
        content_type = message.document.mime_type or content_type
        import io
        buf = io.BytesIO()
        await message.bot.download(message.document.file_id, destination=buf)
        file_bytes = buf.getvalue()
    elif message.photo:
        largest = message.photo[-1]
        file_name = f"receipt_{message.from_user.id}.jpg"
        content_type = "image/jpeg"
        import io
        buf = io.BytesIO()
        await message.bot.download(largest.file_id, destination=buf)
        file_bytes = buf.getvalue()

    if not file_bytes or not file_name:
        return

    # Supabase'e yükle
    public_url = await supa.upload_receipt(filename=file_name, content=file_bytes, content_type=content_type)
    await supa.set_payment_status(message.from_user.id, status="pending", receipt_url=public_url)

    await message.answer("Dekont yüklendi. Onay sonrası gruba ekleneceksiniz.")


@user_router.callback_query(F.data == "pay:done")
async def payment_done(callback: CallbackQuery, supa: SupabaseClient):
    await supa.set_payment_status(callback.from_user.id, status="pending")
    await callback.message.answer("Ödemeniz kontrol için sıraya alındı. Dekont paylaştıysanız daha hızlı onaylanır.")
    await callback.answer()


