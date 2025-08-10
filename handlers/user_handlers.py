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
import asyncio

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
        
        # Veritabanından mesajları yükle
        welcome_messages = await self.db.get_welcome_messages()
        
        if not welcome_messages:
            # Varsayılan mesajları ekle
            await self._create_default_messages()
            welcome_messages = await self.db.get_welcome_messages()
        
        # Mesajları sırayla göster
        for i, msg in enumerate(welcome_messages):
            await message.answer(msg['content'])
            
            # Son mesaj değilse bekle
            if i < len(welcome_messages) - 1:
                await asyncio.sleep(msg.get('delay', 1.0))
        
        # Sorulara geç
        await self.start_questions(message, state)

    async def _create_default_messages(self):
        """Varsayılan mesajları oluşturur"""
        default_messages = [
            {
                'type': 'welcome',
                'title': 'Hoş Geldin',
                'content': """👋 Merhaba! Kompass Network'e hoş geldin.

Burası sıradan bir gelişim grubu değil.  
Burada, kendine liderlik etmek isteyen insanların oluşturduğu özel bir topluluktasın.

Sen buraya rastgele gelmedin.  
Bir şeyleri değiştirmek istediğin için buradasın.  
Hazırsan... birlikte başlayalım. 🔥""",
                'order_index': 1,
                'delay': 1.0
            },
            {
                'type': 'welcome',
                'title': 'Kompass Network Nedir?',
                'content': """📍 Peki Kompass Network nedir?

Kompass Network; Karmaşık bilgilerle zaman kaybettirmeden, sade, uygulanabilir ve yüksek değerli içerikler sunarak; bireylerin öz disiplin kazanmasını, zihinsel farkındalığını artırmasını, hedeflerine ulaşmasını ve sürdürülebilir bir gelişim süreci içinde eyleme geçmesini sağlamak.

Burada:
✅ Haftada 1 Konuklu/Konuksuz Canlı yayınlar
✅ Haftada 1 Soru/Cevap Etkinlikleri
✅ Konu başlıklarıyla sistematik ilerlemeler
✅ E-Kitaplar ve Pdfler
✅ Sıralama ve Rozet sistemleri
✅ Ayın konusuna göre kitap özetleri
✅ Uygulanabilir sistemler  
✅ Özel PDF'ler ve rehberler  
✅ Sadece üyelerin erişebileceği içerikler

Ama en önemlisi:  
✨ Burada yalnız değilsin  
✨ Burada gelişim bilinçli  
✨ Burada kendine liderlik etmen için her şey hazır

Şimdi birkaç soru soracağım.  
Çünkü herkesin yolu farklı… Senin yönünü birlikte bulalım. 🧭""",
                'order_index': 2,
                'delay': 1.0
            }
        ]
        
        for msg in default_messages:
            await self.db.add_message(**msg)
    
    async def show_promotion(self, callback: CallbackQuery, state: FSMContext):
        """Tanıtım mesajını gösterir (artık kullanılmıyor)"""
        # Bu metod artık kullanılmıyor, mesajlar direkt start_command'da gösteriliyor
        await callback.message.edit_text("✅ Tanıtım tamamlandı! Şimdi sorulara geçiyoruz...")
        
        # Sorulara başla
        await self.start_questions(callback.message, state)
    
    async def start_questions(self, message: Message, state: FSMContext):
        """Ana menüyü gösterir"""
        # Ana menü butonlarını oluştur
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="❓ Sorulara Başla", callback_data="start_questions")
        keyboard.button(text="❓ SSS", callback_data="show_sss")
        keyboard.adjust(1)  # Her satırda 1 buton
        
        await message.answer(
            "🎯 **Ana Menü**\n\n"
            "Aşağıdaki seçeneklerden birini seçin:",
            reply_markup=keyboard.as_markup()
        )
    
    async def show_sss(self, callback: CallbackQuery, state: FSMContext):
        """SSS mesajını gösterir"""
        # Veritabanından SSS mesajını yükle
        sss_messages = await self.db.get_messages_by_type('sss')
        
        if not sss_messages:
            # Varsayılan SSS mesajını ekle
            await self._create_default_sss_message()
            sss_messages = await self.db.get_messages_by_type('sss')
        
        if sss_messages:
            # İlk SSS mesajını göster (genellikle tek bir SSS mesajı olur)
            sss_message = sss_messages[0]
            await callback.message.answer(sss_message['content'])
        else:
            await callback.message.answer("❌ SSS bilgisi bulunamadı. Lütfen admin ile iletişime geçin.")
        
        await callback.answer()
    
    async def _create_default_sss_message(self):
        """Varsayılan SSS mesajını oluşturur"""
        default_sss_message = {
            'type': 'sss',
            'title': 'Sık Sorulan Sorular',
            'content': """❓ **Sık Sorulan Sorular (SSS)**

🤔 **Kompass Network nedir?**
Kompass Network, bireylerin öz disiplin kazanmasını, zihinsel farkındalığını artırmasını ve hedeflerine ulaşmasını sağlayan bir gelişim topluluğudur.

💰 **Üyelik ücreti ne kadar?**
Üyelik ücretleri hakkında detaylı bilgi için ödeme kısmından bilgi alabilirsiniz.

⏰ **Canlı yayınlar ne zaman?**
Haftada 1 kez konuklu veya konuksuz canlı yayınlar düzenlenmektedir.

❓ **Başka sorularım var?**
Ek sorularınız için admin ile iletişime geçebilirsiniz.""",
            'order_index': 1,
            'delay': 1.0
        }
        
        await self.db.add_message(**default_sss_message)
    
    async def start_questions_flow(self, callback: CallbackQuery, state: FSMContext):
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
            await callback.message.answer(f"❓ Soru 1: {question['question_text']}")
        else:
            await callback.message.answer("❌ Soru bulunamadı. Lütfen admin ile iletişime geçin.")
        
        await callback.answer()
    
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
            await message.answer(f"❓ Soru {next_index + 1}: {next_question['question_text']}")
        else:
            # Sorular bitti, ödeme kısmına geç
            await self.show_payment(message, state)
    
    async def show_payment(self, message: Message, state: FSMContext):
        """Ödeme kısmını gösterir"""
        # Veritabanından ödeme mesajlarını yükle
        payment_messages = await self.db.get_payment_messages()
        
        if not payment_messages:
            # Varsayılan ödeme mesajlarını ekle
            await self._create_default_payment_messages()
            payment_messages = await self.db.get_payment_messages()
        
        # Mesajları sırayla göster
        for i, msg in enumerate(payment_messages):
            # Mesaj içeriğindeki {payment_link} placeholder'ını gerçek link ile değiştir
            formatted_content = await self._format_message_with_payment_link(msg['content'])
            await message.answer(formatted_content)
            
            # Son mesaj değilse bekle
            if i < len(payment_messages) - 1:
                await asyncio.sleep(msg.get('delay', 1.0))
        
        # Ödeme mesajlarından sonra butonları göster
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="✅ Ödeme Yapıldı", callback_data="payment_done")
        keyboard.button(text="📎 Dekont Ekle(Hızlı Onaylanır)", callback_data="add_receipt")
        keyboard.adjust(1)  # Her satırda 1 buton
        
        await message.answer(
            "💳Ödeme Sonrası İşlemler\n\n"
            "Ödemenizi yaptıysanız aşağıdaki butonlardan birini seçin:",
            reply_markup=keyboard.as_markup()
        )

    async def _create_default_payment_messages(self):
        """Varsayılan ödeme mesajlarını oluşturur"""
        default_payment_messages = [
            {
                'type': 'payment',
                'title': 'Teşekkür',
                'content': """Teşekkür ederim. Cevapların ulaştı ✅

Kompass Network tam da senin gibi düşünen, hisseden ve gelişmek isteyen insanlarla dolu.  
Ve artık hazırsın...""",
                'order_index': 1,
                'delay': 1.0
            },
            {
                'type': 'payment',
                'title': 'Üyelik Başlat',
                'content': """Şimdi sana özel üyeliğini başlatmak için sadece bir adım kaldı.

Aşağıdaki linkten Kompass Network'e katılabilirsin.  
📎 {payment_link}

Şimdi katıl → ve kendine liderlik etmeye başla.""",
                'order_index': 2,
                'delay': 1.0
            }
        ]
        
        for msg in default_payment_messages:
            await self.db.add_message(**msg)

    async def _show_payment_link(self, message: Message):
        """Ödeme linkini gösterir - artık kullanılmıyor, mesaj içeriğinde entegre edildi"""
        pass

    async def _get_payment_link(self):
        """Bot ayarlarından ödeme linkini alır"""
        settings = await self.db.get_bot_settings()
        return settings.get('shopier_payment_url') if settings else None

    async def _format_message_with_payment_link(self, content: str) -> str:
        """Mesaj içeriğindeki {payment_link} placeholder'ını gerçek link ile değiştirir"""
        payment_url = await self._get_payment_link()
        
        if payment_url:
            # Placeholder'ı gerçek link ile değiştir
            formatted_content = content.replace('{payment_link}', payment_url)
        else:
            # Link yoksa placeholder'ı kaldır ve uyarı ekle
            formatted_content = content.replace('{payment_link}', '💳 Ödeme linki henüz ayarlanmamış. Lütfen admin ile iletişime geçin.')
        
        return formatted_content
    
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

@router.callback_query(F.data == "show_sss")
async def show_sss(callback: CallbackQuery, state: FSMContext):
    """SSS gösterme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.show_sss(callback, state)

@router.callback_query(F.data == "start_questions")
async def start_questions_flow(callback: CallbackQuery, state: FSMContext):
    """Sorulara başlama handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.start_questions_flow(callback, state)

@router.message(Command("help"))
async def help_command(message: Message):
    db = DatabaseService()
    settings = await db.get_bot_settings()
    text = settings.get('help_message') or "Yardım: /start, /admin, /help"
    await message.answer(text)
