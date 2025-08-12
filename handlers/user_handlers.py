"""
Kullanıcı Handler'ları
Bu dosya kullanıcı etkileşimlerini yönetir.
"""

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List
import json
from datetime import datetime
import asyncio

from config import Config
from services.database import DatabaseService
from services.file_service import FileService
from services.group_service import GroupService

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
    
    async def start_command(self, message: types.Message, state: FSMContext):
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
    
    async def show_promotion(self, callback: types.CallbackQuery, state: FSMContext):
        """Tanıtım mesajını gösterir (artık kullanılmıyor)"""
        # Bu metod artık kullanılmıyor, mesajlar direkt start_command'da gösteriliyor
        await callback.message.edit_text("✅ Tanıtım tamamlandı! Şimdi sorulara geçiyoruz...")
        
        # Sorulara başla
        await self.start_questions(callback.message, state)
    
    async def start_questions(self, message: types.Message, state: FSMContext):
        """Ana menüyü gösterir"""
        # Ana menü butonlarını oluştur
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❓ Sorulara Başla", callback_data="start_questions")],
            [InlineKeyboardButton(text="❓ SSS", callback_data="show_sss")]
        ])
        
        await message.answer(
            "🎯 **Ana Menü**\n\n"
            "Aşağıdaki seçeneklerden birini seçin:",
            reply_markup=keyboard
        )
    
    async def show_sss(self, callback: types.CallbackQuery, state: FSMContext):
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
    
    async def start_questions_flow(self, callback: types.CallbackQuery, state: FSMContext):
        """Sorulara başlar"""
        questions = await self.db.get_questions()
        
        if not questions:
            # Varsayılan soruları ekle
            for question in Config.DEFAULT_QUESTIONS:
                await self.db.add_question(question)
            questions = await self.db.get_questions()
        
        # İlk soruyu sor
        if questions:
            await state.set_state("answering_questions")
            await state.update_data(current_question_index=0, questions=questions)
            
            question = questions[0]
            await callback.message.answer(f"❓ Soru 1: {question['question_text']}")
        else:
            await callback.message.answer("❌ Soru bulunamadı. Lütfen admin ile iletişime geçin.")
        
        await callback.answer()
    
    async def handle_answer(self, message: types.Message, state: FSMContext):
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
    
    async def show_payment(self, message: types.Message, state: FSMContext):
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📎 Ödeme Dekontu Ekle(ss veya pdf)", callback_data="add_receipt")]
        ])
        
        await message.answer(
            "💳Ödeme Sonrası İşlemler\n\n"
            "Ödemenizi yaptıysanız aşağıdaki butonlardan birini seçin:",
            reply_markup=keyboard
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

    async def _show_payment_link(self, message: types.Message):
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
    
    async def payment_done(self, callback: types.CallbackQuery, state: FSMContext):
        """Ödeme yapıldı butonuna tıklandığında"""
        user_id = callback.from_user.id
        
        await callback.message.edit_text("✅ Ödeme bildiriminiz alındı. Admin onayı bekleniyor...")
        
        # Admin'e bildir
        await self.notify_admin_payment(user_id, callback.message.bot)
        
        await state.clear()
    
    async def add_receipt(self, callback: types.CallbackQuery, state: FSMContext):
        """Dekont ekleme butonuna tıklandığında"""
        print(f"DEBUG: add_receipt çağrıldı - User ID: {callback.from_user.id}")
        
        await callback.message.edit_text(
            "📎 Lütfen ödeme dekontunuzu (PDF, JPG, PNG) gönderin.\n\n"
            "💡 **İpucu:** Dekontunuzu fotoğraf olarak çekip gönderebilirsiniz."
        )
        
        print(f"DEBUG: State set ediliyor: waiting_for_receipt")
        await state.set_state("waiting_for_receipt")
        
        # State'i kontrol et
        current_state = await state.get_state()
        print(f"DEBUG: Current state: {current_state}")
        
        await callback.answer()
    
    async def handle_receipt(self, message: types.Message, state: FSMContext):
        """Dekont dosyasını işler"""
        user_id = message.from_user.id
        current_state = await state.get_state()
        print(f"DEBUG: handle_receipt çağrıldı - User ID: {user_id}, Current State: {current_state}")
        
        if not message.document and not message.photo:
            print(f"DEBUG: Geçersiz dosya türü - Document: {message.document}, Photo: {message.photo}")
            await message.answer("❌ Lütfen geçerli bir dosya gönderin (PDF, JPG, PNG).")
            return
        
        try:
            # Dosyayı al
            if message.document:
                file = message.document
                file_name = file.file_name
                file_id = file.file_id
                print(f"DEBUG: Document dosyası - Name: {file_name}, ID: {file_id}")
            else:
                # Fotoğraf
                photo = message.photo[-1]
                file_id = photo.file_id
                file_name = f"receipt_{user_id}_{photo.file_id}.jpg"
                print(f"DEBUG: Photo dosyası - Name: {file_name}, ID: {file_id}")
            
            # Dosyayı indir
            print(f"DEBUG: Dosya indiriliyor...")
            file_info = await message.bot.get_file(file_id)
            file_data = await message.bot.download_file(file_info.file_path)
            print(f"DEBUG: Dosya indirildi - Boyut: {len(file_data.read()) if hasattr(file_data, 'read') else 'N/A'}")
            
            # Dosya pointer'ı başa al
            if hasattr(file_data, 'seek'):
                file_data.seek(0)
            
            # Dosyayı kaydet
            print(f"DEBUG: FileService.save_file çağrılıyor...")
            file_url = await self.file_service.save_file(
                file_data.read() if hasattr(file_data, 'read') else file_data,
                file_name,
                user_id
            )
            print(f"DEBUG: FileService.save_file sonucu: {file_url}")
            
            if file_url:
                # Dekontu veritabanına kaydet
                print(f"DEBUG: DatabaseService.save_receipt çağrılıyor...")
                receipt_result = await self.db.save_receipt(user_id, file_url, file_name)
                print(f"DEBUG: DatabaseService.save_receipt sonucu: {receipt_result}")
                
                print(f"DEBUG: Başarı mesajı gönderiliyor...")
                await message.answer(
                    "✅ Dekontunuz başarıyla yüklendi!\n\n"
                    "📋 Admin onayı bekleniyor. Onaylandıktan sonra gruba davet edileceksiniz."
                )
                print(f"DEBUG: Başarı mesajı gönderildi")
                
                # Admin'e bildir
                print(f"DEBUG: Admin bildirimi gönderiliyor...")
                await self.notify_admin_receipt(user_id, file_name, message.bot)
                print(f"DEBUG: Admin bildirimi gönderildi")
                
                await state.clear()
                print(f"DEBUG: State temizlendi")
            else:
                print(f"DEBUG: FileService.save_file None döndü")
                await message.answer("❌ Dosya yükleme hatası. Lütfen tekrar deneyin.")
                
        except Exception as e:
            print(f"DEBUG: Exception yakalandı: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
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

def dp(bot, dispatcher):
    """Dispatcher'a handler'ları ekler"""
    # Message handlers - Tüm mesajları yakala, içeride state kontrolü yap
    dispatcher.register_message_handler(start_command, commands=["start"])
    dispatcher.register_message_handler(help_command, commands=["help"])
    dispatcher.register_message_handler(handle_all_messages)  # Tüm mesajları yakala
    
    # Callback query handlers
    dispatcher.register_callback_query_handler(show_promotion, lambda c: c.data == "show_promotion", state="*")
    dispatcher.register_callback_query_handler(payment_done, lambda c: c.data == "payment_done", state="*")
    dispatcher.register_callback_query_handler(add_receipt, lambda c: c.data == "add_receipt", state="*")
    dispatcher.register_callback_query_handler(show_sss, lambda c: c.data == "show_sss", state="*")
    dispatcher.register_callback_query_handler(start_questions_flow, lambda c: c.data == "start_questions", state="*")

# Handler fonksiyonları
async def start_command(message: types.Message, state: FSMContext):
    """Start komutu handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.start_command(message, state)

async def show_promotion(callback: types.CallbackQuery, state: FSMContext):
    """Tanıtım gösterme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.show_promotion(callback, state)

async def handle_answer(message: types.Message, state: FSMContext):
    """Cevap işleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.handle_answer(message, state)

async def payment_done(callback: types.CallbackQuery, state: FSMContext):
    """Ödeme yapıldı handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.payment_done(callback, state)

async def add_receipt(callback: types.CallbackQuery, state: FSMContext):
    """Dekont ekleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.add_receipt(callback, state)

async def handle_receipt(message: types.Message, state: FSMContext):
    """Dekont işleme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(message.bot))
    await handler.handle_receipt(message, state)

async def show_sss(callback: types.CallbackQuery, state: FSMContext):
    """SSS gösterme handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.show_sss(callback, state)

async def start_questions_flow(callback: types.CallbackQuery, state: FSMContext):
    """Sorulara başlama handler'ı"""
    handler = UserHandler(DatabaseService(), FileService(), GroupService(callback.message.bot))
    await handler.start_questions_flow(callback, state)

async def handle_all_messages(message: types.Message, state: FSMContext):
    """Tüm mesajları yakalar ve state'e göre yönlendirir"""
    current_state = await state.get_state()
    print(f"DEBUG: handle_all_messages çağrıldı!")
    print(f"DEBUG: Message type: {message.content_type}")
    print(f"DEBUG: Message text: {message.text}")
    print(f"DEBUG: Current state: {current_state}")
    print(f"DEBUG: User ID: {message.from_user.id}")
    
    # Handler instance'ı oluştur
    handler = UserHandler()
    print(f"DEBUG: Handler instance oluşturuldu")
    
    if current_state == "answering_questions":
        print(f"DEBUG: answering_questions state'inde, handle_answer çağrılıyor...")
        # Soru cevaplama state'inde
        await handler.handle_answer(message, state)
    elif current_state == "waiting_for_receipt":
        print(f"DEBUG: waiting_for_receipt state'inde, handle_receipt çağrılıyor...")
        # Dekont bekleme state'inde
        await handler.handle_receipt(message, state)
    else:
        # State yoksa veya bilinmeyen state'de
        print(f"DEBUG: Bilinmeyen state: {current_state}")
        print(f"DEBUG: Mesaj işlenmedi")

async def help_command(message: types.Message):
    db = DatabaseService()
    settings = await db.get_bot_settings()
    text = settings.get('help_message') or "Yardım: /start, /admin, /help"
    await message.answer(text)
