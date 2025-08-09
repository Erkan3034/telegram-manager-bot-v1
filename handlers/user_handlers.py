"""
Kullanıcı Handler'ları
Bu dosya kullanıcı etkileşimlerini yönetir.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Dict, List
import json
from datetime import datetime

from config import Config
from services.database import DatabaseService
from services.file_service import FileService
from services.group_service import GroupService

router = Router()

# FSM States
class UserStates(StatesGroup):
    """Kullanıcı durumları"""
    waiting_for_questions = State()
    answering_questions = State()
    waiting_for_receipt = State()

class UserHandler:
    """Kullanıcı handler sınıfı"""
    
    def __init__(self, database: DatabaseService, file_service: FileService, group_service: GroupService):
        self.db = database
        self.file_service = file_service
        self.group_service = group_service
    
    async def start_command(self, message: Message, state: FSMContext):
        """Kullanıcı /start komutunu işler"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        # Kullanıcıyı veritabanına kaydet
        user = await self.db.get_user(user_id)
        if not user:
            await self.db.create_user(
                user_id=user_id,
                username=username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
        
        # Hoş geldin mesajı (db'deki ayarlar öncelikli) ve {kullanıcı_adi} desteği
        settings = await self.db.get_bot_settings()
        raw_text = settings.get('start_message') or Config.WELCOME_MESSAGE
        # Türkçe yer tutucu desteği
        raw_text = raw_text.replace('{kullanıcı_adi}', '{username}')
        try:
            welcome_text = raw_text.format(username=username)
        except Exception:
            # Hatalı yer tutucu varsa en azından username'i basalım
            welcome_text = raw_text.replace('{username}', username)
        await message.answer(welcome_text)
        
        # Tanıtım butonu
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Tanıtımı Gör", callback_data="show_promotion")
        
        intro = settings.get('intro_message') or Config.INTRO_MESSAGE
        await message.answer(intro, reply_markup=builder.as_markup())
    
    async def show_promotion(self, callback: CallbackQuery, state: FSMContext):
        """Tanıtım mesajını gösterir"""
        settings = await self.db.get_bot_settings()
        promo = settings.get('promotion_message') or Config.PROMOTION_MESSAGE
        await callback.message.edit_text(promo)
        
        # Sorulara başla
        await self.start_questions(callback.message, state)
    
    async def start_questions(self, message: Message, state: FSMContext):
        """Sorulara başlar"""
        questions = await self.db.get_questions()
        
        if not questions:
            # Varsayılan soruları ekle
            for question in Config.DEFAULT_QUESTIONS:
                await self.db.add_question(question)
            questions = await self.db.get_questions()
        
        # İlk soruyu sor
        if questions:
            await state.set_state(UserStates.answering_questions)
            await state.update_data(current_question_index=0, questions=questions)
            
            question = questions[0]
            await message.answer(f"❓ **Soru 1:** {question['question_text']}")
        else:
            await message.answer("❌ Soru bulunamadı. Lütfen admin ile iletişime geçin.")
    
    async def handle_answer(self, message: Message, state: FSMContext):
        """Kullanıcı cevabını işler"""
        user_id = message.from_user.id
        data = await state.get_data()
        
        current_index = data.get('current_question_index', 0)
        questions = data.get('questions', [])
        
        if current_index >= len(questions):
            await message.answer("❌ Beklenmeyen hata oluştu.")
            return
        
        # Cevabı kaydet
        question = questions[current_index]
        await self.db.save_answer(user_id, question['id'], message.text)
        
        # Sonraki soruya geç
        next_index = current_index + 1
        
        if next_index < len(questions):
            # Sonraki soru
            await state.update_data(current_question_index=next_index)
            next_question = questions[next_index]
            await message.answer(f"❓ **Soru {next_index + 1}:** {next_question['question_text']}")
        else:
            # Sorular bitti, ödeme kısmına geç
            await self.show_payment(message, state)
    
    async def show_payment(self, message: Message, state: FSMContext):
        """Ödeme kısmını gösterir"""
        # Ödeme kaydı oluştur
        user_id = message.from_user.id
        await self.db.create_payment(user_id)
        
        settings = await self.db.get_bot_settings()
        custom_payment = settings.get('payment_message')
        payment_text = custom_payment or f"""
💳 **Ödeme Bilgileri**

💰 **Tutar:** 99.99 TL
🔗 **Ödeme Linki:** {Config.SHOPIER_PAYMENT_URL}

📋 Ödeme yaptıktan sonra aşağıdaki butonlardan birini kullanın:
        """
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Ödeme Yaptım", callback_data="payment_done")
        builder.button(text="📎 Dekont Ekle", callback_data="add_receipt")
        
        await message.answer(payment_text, reply_markup=builder.as_markup())
    
    async def payment_done(self, callback: CallbackQuery, state: FSMContext):
        """Ödeme yapıldı butonuna tıklandığında"""
        user_id = callback.from_user.id
        
        await callback.message.edit_text("✅ Ödeme bildiriminiz alındı. Admin onayı bekleniyor...")
        
        # Admin'e bildir
        await self.notify_admin_payment(user_id, callback.message.bot)
        
        await state.clear()
    
    async def add_receipt(self, callback: CallbackQuery, state: FSMContext):
        """Dekont ekleme butonuna tıklandığında"""
        await callback.message.edit_text(
            "📎 Lütfen ödeme dekontunuzu (PDF, JPG, PNG) gönderin.\n\n"
            "💡 **İpucu:** Dekontunuzu fotoğraf olarak çekip gönderebilirsiniz."
        )
        await state.set_state(UserStates.waiting_for_receipt)
    
    async def handle_receipt(self, message: Message, state: FSMContext):
        """Dekont dosyasını işler"""
        user_id = message.from_user.id
        
        if not message.document and not message.photo:
            await message.answer("❌ Lütfen geçerli bir dosya gönderin (PDF, JPG, PNG).")
            return
        
        try:
            # Dosyayı al
            if message.document:
                file = message.document
                file_name = file.file_name
                file_id = file.file_id
            else:
                # Fotoğraf
                photo = message.photo[-1]
                file_id = photo.file_id
                file_name = f"receipt_{user_id}_{photo.file_id}.jpg"
            
            # Dosyayı indir
            file_info = await message.bot.get_file(file_id)
            file_data = await message.bot.download_file(file_info.file_path)
            
            # Dosyayı kaydet
            file_url = await self.file_service.save_file(
                file_data.read(),
                file_name,
                user_id
            )
            
            if file_url:
                # Dekontu veritabanına kaydet
                await self.db.save_receipt(user_id, file_url, file_name)
                
                await message.answer(
                    "✅ Dekontunuz başarıyla yüklendi!\n\n"
                    "📋 Admin onayı bekleniyor. Onaylandıktan sonra gruba davet edileceksiniz."
                )
                
                # Admin'e bildir
                await self.notify_admin_receipt(user_id, file_name, message.bot)
                
                await state.clear()
            else:
                await message.answer("❌ Dosya yükleme hatası. Lütfen tekrar deneyin.")
                
        except Exception as e:
            print(f"Dekont işleme hatası: {e}")
            await message.answer("❌ Dosya işleme hatası. Lütfen tekrar deneyin.")
    
    async def notify_admin_payment(self, user_id: int, bot):
        """Admin'e ödeme bildirimi gönderir"""
        try:
            user = await self.db.get_user(user_id)
            username = user['username'] if user else str(user_id)
            
            notification = f"""
💰 **Yeni Ödeme Bildirimi**

👤 **Kullanıcı:** @{username} ({user_id})
💳 **Durum:** Ödeme yapıldı (bekleniyor)
⏰ **Zaman:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Admin panelinden onaylayabilirsiniz.
            """
            
            for admin_id in Config.ADMIN_IDS:
                await bot.send_message(chat_id=admin_id, text=notification)
                
        except Exception as e:
            print(f"Admin ödeme bildirimi hatası: {e}")
    
    async def notify_admin_receipt(self, user_id: int, file_name: str, bot):
        """Admin'e dekont bildirimi gönderir"""
        try:
            user = await self.db.get_user(user_id)
            username = user['username'] if user else str(user_id)
            
            notification = f"""
📎 **Yeni Dekont Bildirimi**

👤 **Kullanıcı:** @{username} ({user_id})
📄 **Dosya:** {file_name}
⏰ **Zaman:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Admin panelinden onaylayabilirsiniz.
            """
            
            for admin_id in Config.ADMIN_IDS:
                await bot.send_message(chat_id=admin_id, text=notification)
                
        except Exception as e:
            print(f"Admin dekont bildirimi hatası: {e}")

# Router'a handler'ları ekle
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Start komutu handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.start_command(message, state)

@router.callback_query(F.data == "show_promotion")
async def show_promotion(callback: CallbackQuery, state: FSMContext):
    """Tanıtım gösterme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.show_promotion(callback, state)

@router.message(UserStates.answering_questions)
async def handle_answer(message: Message, state: FSMContext):
    """Cevap işleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.handle_answer(message, state)

@router.callback_query(F.data == "payment_done")
async def payment_done(callback: CallbackQuery, state: FSMContext):
    """Ödeme yapıldı handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.payment_done(callback, state)

@router.callback_query(F.data == "add_receipt")
async def add_receipt(callback: CallbackQuery, state: FSMContext):
    """Dekont ekleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.add_receipt(callback, state)

@router.message(UserStates.waiting_for_receipt)
async def handle_receipt(message: Message, state: FSMContext):
    """Dekont işleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.handle_receipt(message, state)

@router.message(Command("help"))
async def help_command(message: Message):
    db = DatabaseService()
    settings = await db.get_bot_settings()
    text = settings.get('help_message') or "Yardım: /start, /admin, /help"
    await message.answer(text)
