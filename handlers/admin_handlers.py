"""
Admin Handler'ları
Bu dosya admin işlemlerini yönetir.
"""

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
import json

from config import Config
from services.database import DatabaseService
from services.group_service import GroupService

# FSM States
class AdminStates(StatesGroup):
    """Admin durumları"""
    adding_question = State()
    editing_question = State()

class AdminHandler:
    """Admin handler sınıfı"""
    
    def __init__(self, database: DatabaseService, group_service: GroupService):
        self.db = database
        self.group_service = group_service
    
    def is_admin(self, user_id: int) -> bool:
        """Kullanıcının admin olup olmadığını kontrol eder"""
        return user_id in Config.ADMIN_IDS
    
    async def admin_panel(self, message: types.Message):
        """Admin panelini gösterir"""
        if not self.is_admin(message.from_user.id):
            await message.answer("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❓ Soruları Yönet", callback_data="admin_questions")],
            [InlineKeyboardButton(text="💰 Ödeme Yapanlar", callback_data="admin_payments")],
            [InlineKeyboardButton(text="👥 Üyeler", callback_data="admin_members")],
            [InlineKeyboardButton(text="📊 İstatistikler", callback_data="admin_stats")]
        ])
        
        await message.answer(
            "🔧 **Admin Paneli**\n\n"
            "Aşağıdaki seçeneklerden birini seçin:",
            reply_markup=keyboard
        )
    
    async def show_questions(self, callback: types.CallbackQuery):
        """Soruları gösterir"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        questions = await self.db.get_questions()
        
        if not questions:
            await callback.message.edit_text("❌ Henüz soru eklenmemiş.")
            return
        
        text = "❓ **Mevcut Sorular:**\n\n"
        keyboard_buttons = []
        
        for i, question in enumerate(questions, 1):
            text += f"{i}. {question['question_text']}\n"
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"🗑️ Sil {i}",
                callback_data=f"delete_question_{question['id']}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(text="➕ Yeni Soru Ekle", callback_data="add_question")])
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    async def add_question_form(self, callback: types.CallbackQuery, state: FSMContext):
        """Yeni soru ekleme formunu gösterir"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        await state.set_state(AdminStates.adding_question)
        await callback.message.edit_text(
            "❓ **Yeni Soru Ekleme**\n\n"
            "Lütfen eklemek istediğiniz soruyu yazın:"
        )
    
    async def handle_new_question(self, message: types.Message, state: FSMContext):
        """Yeni soruyu işler"""
        if not self.is_admin(message.from_user.id):
            await message.answer("❌ Yetkiniz yok.")
            return
        
        question_text = message.text.strip()
        
        if len(question_text) < 3:
            await message.answer("❌ Soru en az 3 karakter olmalıdır.")
            return
        
        # Soruyu ekle
        question = await self.db.add_question(question_text)
        
        if question:
            await message.answer(f"✅ Soru başarıyla eklendi: {question_text}")
        else:
            await message.answer("❌ Soru eklenirken hata oluştu.")
        
        await state.clear()
        await self.admin_panel(message)
    
    async def delete_question(self, callback: types.CallbackQuery):
        """Soruyu siler"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        question_id = int(callback.data.split('_')[-1])
        
        success = await self.db.delete_question(question_id)
        
        if success:
            await callback.answer("✅ Soru silindi.", show_alert=True)
        else:
            await callback.answer("❌ Soru silinirken hata oluştu.", show_alert=True)
        
        # Soruları yeniden göster
        await self.show_questions(callback)
    
    async def show_payments(self, callback: types.CallbackQuery):
        """Ödeme yapanları gösterir"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        payments = await self.db.get_pending_payments()
        receipts = await self.db.get_pending_receipts()
        
        if not payments and not receipts:
            await callback.message.edit_text("❌ Bekleyen ödeme veya dekont bulunmuyor.")
            return
        
        text = "💰 **Bekleyen Ödemeler ve Dekontlar:**\n\n"
        keyboard_buttons = []
        
        # Ödemeler
        for payment in payments:
            user = payment.get('users', {})
            username = user.get('username', 'Bilinmeyen')
            text += f"💳 **Kullanıcı:** @{username}\n"
            text += f"💰 **Tutar:** {payment['amount']} TL\n"
            text += f"⏰ **Tarih:** {payment['created_at'][:10]}\n\n"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"✅ Onayla {username}",
                callback_data=f"approve_payment_{payment['id']}"
            )])
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"❌ Reddet {username}",
                callback_data=f"reject_payment_{payment['id']}"
            )])
        
        # Dekontlar
        for receipt in receipts:
            user = receipt.get('users', {})
            username = user.get('username', 'Bilinmeyen')
            text += f"📎 **Dekont:** @{username}\n"
            text += f"📄 **Dosya:** {receipt['file_name']}\n"
            text += f"⏰ **Tarih:** {receipt['created_at'][:10]}\n\n"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"✅ Onayla {username}",
                callback_data=f"approve_receipt_{receipt['id']}"
            )])
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"❌ Reddet {username}",
                callback_data=f"reject_receipt_{receipt['id']}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    async def approve_payment(self, callback: types.CallbackQuery):
        """Ödemeyi onaylar"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        payment_id = int(callback.data.split('_')[-1])
        
        # Ödeme durumunu güncelle
        success = await self.db.update_payment_status(payment_id, 'approved')
        
        if success:
            payment = await self.db.get_payment(payment_id)
            if payment:
                user_id = payment['user_id']
                # Sadece dekont onayı ile gruba alınacak; kullanıcıdan dekont talep et
                try:
                    await callback.message.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "💳 Ödemeniz alındı.\n\n"
                            "📎 Lütfen ödeme dekontunuzu bu sohbete PDF/JPG/PNG olarak gönderin."
                        )
                    )
                except Exception:
                    pass
                await callback.answer("✅ Ödeme işaretlendi. Kullanıcıdan dekont istendi.", show_alert=True)
            else:
                await callback.answer("❌ Ödeme bilgisi bulunamadı.", show_alert=True)
        else:
            await callback.answer("❌ Ödeme onaylanırken hata oluştu.", show_alert=True)
        
        # Ödemeleri yeniden göster
        await self.show_payments(callback)
    
    async def reject_payment(self, callback: types.CallbackQuery):
        """Ödemeyi reddeder"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        payment_id = int(callback.data.split('_')[-1])
        
        # Ödeme durumunu güncelle
        success = await self.db.update_payment_status(payment_id, 'rejected')
        
        if success:
            # Kullanıcıya bilgi gönder
            payment = await self.db.get_payment(payment_id)
            if payment:
                user_id = payment['user_id']
                await callback.message.bot.send_message(
                    chat_id=user_id,
                    text="❌ Ödemeniz reddedildi. Lütfen admin ile iletişime geçin."
                )
            
            await callback.answer("❌ Ödeme reddedildi.", show_alert=True)
        else:
            await callback.answer("❌ Ödeme reddedilirken hata oluştu.", show_alert=True)
        
        # Ödemeleri yeniden göster
        await self.show_payments(callback)
    
    async def approve_receipt(self, callback: types.CallbackQuery):
        """Dekontu onaylar"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        receipt_id = int(callback.data.split('_')[-1])
        
        # Dekont durumunu güncelle
        success = await self.db.update_receipt_status(receipt_id, 'approved')
        
        if success:
            # Kullanıcıyı gruba ekle
            receipt = await self.db.get_receipt(receipt_id)
            if receipt:
                user_id = receipt['user_id']
                # Kullanıcıya onay mesajı ve davet linki gönder (tek kriter dekont onayı)
                await self.group_service.add_user_to_group(user_id)
                
                await callback.answer("✅ Dekont onaylandı ve kullanıcı gruba davet edildi.", show_alert=True)
            else:
                await callback.answer("❌ Dekont bilgisi bulunamadı.", show_alert=True)
        else:
            await callback.answer("❌ Dekont onaylanırken hata oluştu.", show_alert=True)
        
        # Ödemeleri yeniden göster
        await self.show_payments(callback)
    
    async def reject_receipt(self, callback: types.CallbackQuery):
        """Dekontu reddeder"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        receipt_id = int(callback.data.split('_')[-1])
        
        # Dekont durumunu güncelle
        success = await self.db.update_receipt_status(receipt_id, 'rejected')
        
        if success:
            # Kullanıcıya bilgi gönder
            receipt = await self.db.get_receipt(receipt_id)
            if receipt:
                user_id = receipt['user_id']
                await callback.message.bot.send_message(
                    chat_id=user_id,
                    text="❌ Dekontunuz reddedildi. Lütfen admin ile iletişime geçin."
                )
            
            await callback.answer("❌ Dekont reddedildi.", show_alert=True)
        else:
            await callback.answer("❌ Dekont reddedilirken hata oluştu.", show_alert=True)
        
        # Ödemeleri yeniden göster
        await self.show_payments(callback)
    
    async def show_members(self, callback: types.CallbackQuery):
        """Grup üyelerini gösterir"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        members = await self.db.get_group_members(Config.GROUP_ID)
        
        if not members:
            await callback.message.edit_text("❌ Henüz grup üyesi bulunmuyor.")
            return
        
        text = "👥 **Grup Üyeleri:**\n\n"
        keyboard_buttons = []
        
        for i, member in enumerate(members, 1):
            user = member.get('users', {})
            username = user.get('username', 'Bilinmeyen')
            text += f"{i}. @{username} ({user.get('user_id', 'N/A')})\n"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"🚫 Çıkar {username}",
                callback_data=f"remove_member_{user.get('user_id', 0)}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    async def remove_member(self, callback: types.CallbackQuery):
        """Üyeyi gruptan çıkarır"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        user_id = int(callback.data.split('_')[-1])
        
        # Kullanıcıyı gruptan çıkar
        success = await self.group_service.remove_user_from_group(user_id)
        
        if success:
            await callback.answer("✅ Kullanıcı gruptan çıkarıldı.", show_alert=True)
        else:
            await callback.answer("❌ Kullanıcı çıkarılırken hata oluştu.", show_alert=True)
        
        # Üyeleri yeniden göster
        await self.show_members(callback)
    
    async def show_stats(self, callback: types.CallbackQuery):
        """İstatistikleri gösterir"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Yetkiniz yok.", show_alert=True)
            return
        
        # İstatistikleri hesapla
        total_users = len(await self.db.get_all_users())
        total_payments = len(await self.db.get_all_payments())
        pending_payments = len(await self.db.get_pending_payments())
        total_members = len(await self.db.get_group_members(Config.GROUP_ID))
        
        text = f"""
📊 **Bot İstatistikleri**

👥 **Toplam Kullanıcı:** {total_users}
💰 **Toplam Ödeme:** {total_payments}
⏳ **Bekleyen Ödeme:** {pending_payments}
👤 **Grup Üyesi:** {total_members}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Geri", callback_data="admin_panel")]])
        
        await callback.message.edit_text(text, reply_markup=keyboard)

def dp(bot, dispatcher):
    """Dispatcher'a admin handler'ları ekler"""
    # Message handlers
    dispatcher.register_message_handler(admin_panel, commands=["admin"])
    dispatcher.register_message_handler(handle_new_question, state=AdminStates.adding_question)
    
    # Callback query handlers
    dispatcher.register_callback_query_handler(admin_panel_callback, lambda c: c.data == "admin_panel")
    dispatcher.register_callback_query_handler(show_questions, lambda c: c.data == "admin_questions")
    dispatcher.register_callback_query_handler(add_question_form, lambda c: c.data == "add_question")
    dispatcher.register_callback_query_handler(delete_question, lambda c: c.data and c.data.startswith("delete_question_"))
    dispatcher.register_callback_query_handler(show_payments, lambda c: c.data == "admin_payments")
    dispatcher.register_callback_query_handler(approve_payment, lambda c: c.data and c.data.startswith("approve_payment_"))
    dispatcher.register_callback_query_handler(reject_payment, lambda c: c.data and c.data.startswith("reject_payment_"))
    dispatcher.register_callback_query_handler(approve_receipt, lambda c: c.data and c.data.startswith("approve_receipt_"))
    dispatcher.register_callback_query_handler(reject_receipt, lambda c: c.data and c.data.startswith("reject_receipt_"))
    dispatcher.register_callback_query_handler(show_members, lambda c: c.data == "admin_members")
    dispatcher.register_callback_query_handler(remove_member, lambda c: c.data and c.data.startswith("remove_member_"))
    dispatcher.register_callback_query_handler(show_stats, lambda c: c.data == "admin_stats")

# Handler fonksiyonları
async def admin_panel(message: types.Message):
    """Admin paneli handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(message.bot))
    await handler.admin_panel(message)

async def admin_panel_callback(callback: types.CallbackQuery):
    """Admin paneli callback handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.admin_panel(callback.message)

async def show_questions(callback: types.CallbackQuery):
    """Soruları gösterme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.show_questions(callback)

async def add_question_form(callback: types.CallbackQuery, state: FSMContext):
    """Soru ekleme formu handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.add_question_form(callback, state)

async def handle_new_question(message: types.Message, state: FSMContext):
    """Yeni soru işleme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(message.bot))
    await handler.handle_new_question(message, state)

async def delete_question(callback: types.CallbackQuery):
    """Soru silme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.delete_question(callback)

async def show_payments(callback: types.CallbackQuery):
    """Ödemeleri gösterme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.show_payments(callback)

async def approve_payment(callback: types.CallbackQuery):
    """Ödeme onaylama handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.approve_payment(callback)

async def reject_payment(callback: types.CallbackQuery):
    """Ödeme reddetme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.reject_payment(callback)

async def approve_receipt(callback: types.CallbackQuery):
    """Dekont onaylama handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.approve_receipt(callback)

async def reject_receipt(callback: types.CallbackQuery):
    """Dekont reddetme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.reject_receipt(callback)

async def show_members(callback: types.CallbackQuery):
    """Üyeleri gösterme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.show_members(callback)

async def remove_member(callback: types.CallbackQuery):
    """Üye çıkarma handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.remove_member(callback)

async def show_stats(callback: types.CallbackQuery):
    """İstatistikleri gösterme handler'ı"""
    handler = AdminHandler(DatabaseService(), GroupService(callback.message.bot))
    await handler.show_stats(callback)
