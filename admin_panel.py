from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from services.supabase_client import SupabaseClient
from services.group_service import GroupService


admin_router = Router(name="admin_router")


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


def admin_main_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="Soruları Yönet", callback_data="admin:questions")
    kb.button(text="Ödeme Bekleyenler", callback_data="admin:pending_payments")
    kb.button(text="Üyeler", callback_data="admin:members")
    kb.adjust(1)
    return kb


@admin_router.message(Command("admin"))
async def admin_entry(message: Message, supa: SupabaseClient):
    if not is_admin(message.from_user.id):
        return await message.answer("Bu komut sadece yöneticilere özeldir.")
    await message.answer("Admin Paneline Hoş Geldiniz.", reply_markup=admin_main_keyboard().as_markup())


@admin_router.callback_query(F.data == "admin:questions")
async def admin_questions_menu(callback: CallbackQuery, supa: SupabaseClient):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)

    questions = await supa.list_questions()
    kb = InlineKeyboardBuilder()
    for q in questions:
        kb.button(text=f"❌ Sil: {q['order_index']}", callback_data=f"admin:del_q:{q['id']}")
    kb.button(text="➕ Yeni Soru Ekle", callback_data="admin:add_q")
    kb.button(text="⬅️ Geri", callback_data="admin:back")
    kb.adjust(1)
    text = "Mevcut Sorular:\n" + "\n".join([f"{q['order_index']}. {q['text']}" for q in questions])
    await callback.message.edit_text(text or "Soru bulunamadı.", reply_markup=kb.as_markup())


@admin_router.callback_query(F.data.startswith("admin:del_q:"))
async def admin_delete_question(callback: CallbackQuery, supa: SupabaseClient):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    qid = callback.data.split(":")[-1]
    await supa.delete_question(qid)
    await callback.answer("Soru silindi")
    await admin_questions_menu(callback, supa)


@admin_router.callback_query(F.data == "admin:add_q")
async def admin_add_question_start(callback: CallbackQuery, supa: SupabaseClient):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    await callback.message.edit_text("Yeni soru metnini gönderin. İptal için /admin yazın.")
    await supa.set_admin_state(callback.from_user.id, "awaiting_new_question_text")


@admin_router.message(F.text, ~Command("admin"))
async def admin_add_question_text(message: Message, supa: SupabaseClient):
    # Minimal FSM via DB state to keep dependencies low
    if not is_admin(message.from_user.id):
        return
    state = await supa.get_admin_state(message.from_user.id)
    if state != "awaiting_new_question_text":
        return
    text = message.text.strip()
    await supa.add_question(text)
    await supa.set_admin_state(message.from_user.id, None)
    await message.answer("Soru eklendi.")
    await message.answer("Admin Panel", reply_markup=admin_main_keyboard().as_markup())


@admin_router.callback_query(F.data == "admin:pending_payments")
async def admin_pending_payments(callback: CallbackQuery, supa: SupabaseClient, groups: GroupService):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    pending = await supa.list_pending_payments()
    if not pending:
        return await callback.message.edit_text("Bekleyen ödeme/dosya bulunmuyor.", reply_markup=admin_main_keyboard().as_markup())

    kb = InlineKeyboardBuilder()
    lines = []
    for p in pending:
        user_id = p["telegram_user_id"]
        receipt_url = p.get("receipt_url") or "-"
        lines.append(f"Kullanıcı: {user_id} | Dekont: {receipt_url}")
        kb.button(text=f"✅ Onayla {user_id}", callback_data=f"admin:approve:{user_id}")
        kb.button(text=f"❌ Reddet {user_id}", callback_data=f"admin:reject:{user_id}")
    kb.button(text="⬅️ Geri", callback_data="admin:back")
    kb.adjust(1)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())


@admin_router.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve_payment(callback: CallbackQuery, supa: SupabaseClient, groups: GroupService):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    user_id = int(callback.data.split(":")[-1])
    await supa.set_payment_status(user_id, "approved")
    await groups.add_user_to_group(user_id)
    await supa.add_member(user_id)
    await callback.answer("Onaylandı ve gruba eklendi.")
    await admin_pending_payments(callback, supa, groups)


@admin_router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject_payment(callback: CallbackQuery, supa: SupabaseClient):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    user_id = int(callback.data.split(":")[-1])
    await supa.set_payment_status(user_id, "rejected")
    try:
        await callback.bot.send_message(chat_id=user_id, text="Ödemeniz maalesef reddedildi. Lütfen dekontu kontrol edip tekrar gönderin veya bizimle iletişime geçin.")
    except Exception:
        pass
    await callback.message.answer(f"{user_id} kullanıcısının ödemesi reddedildi.")
    await callback.answer("Reddedildi")
    await admin_pending_payments(callback, supa, None)  # groups unused here


@admin_router.callback_query(F.data == "admin:members")
async def admin_members(callback: CallbackQuery, supa: SupabaseClient):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    members = await supa.list_members()
    text = "Üyeler:\n" + "\n".join([str(m["telegram_user_id"]) for m in members]) if members else "Henüz üye yok."
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Geri", callback_data="admin:back")
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@admin_router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("Yetkiniz yok", show_alert=True)
    await callback.message.edit_text("Admin Paneli", reply_markup=admin_main_keyboard().as_markup())


