"""
Telegram Grup Yönetimi Servisi
Bu dosya Telegram gruplarındaki işlemleri yönetir.
"""

from typing import List, Optional, Dict
from aiogram import Bot
from aiogram.types import ChatMember
from config import Config

class GroupService:
    """Telegram grup yönetimi servisi"""
    
    def __init__(self, bot: Bot):
        """Grup servisini başlatır"""
        self.bot = bot
        self.group_id = Config.GROUP_ID
    
    async def add_user_to_group(self, user_id: int) -> bool:
        """
        Kullanıcıyı gruba ekler ve bilgilendirir
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Başarı durumu
        """
        try:
            # Onay mesajı gönder
            await self.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ Ödemeniz/dekontunuz onaylandı!\n\n"
                    "Şimdi grubumuza katılabilirsiniz. Davet linki birazdan gönderilecek."
                )
            )

            # Kullanıcı için tek kullanımlık davet linki oluştur
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=self.group_id,
                member_limit=1
            )
            
            # Kullanıcıya davet linkini gönder
            await self.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 Tebrikler!\n\n"
                    "Grubumuza katılmak için aşağıdaki linke tıklayın:\n"
                    f"{invite_link.invite_link}"
                )
            )
            
            # Supabase'e 'invited' olarak kaydet
            try:
                from services.database import DatabaseService
                db = DatabaseService()
                await db.add_group_member(user_id=user_id, group_id=self.group_id, status='invited')
            except Exception as _:
                pass
            
            return True
            
        except Exception as e:
            print(f"Kullanıcıyı gruba ekleme hatası: {e}")
            return False
    
    async def remove_user_from_group(self, user_id: int) -> bool:
        """
        Kullanıcıyı gruptan çıkarır
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Başarı durumu
        """
        try:
            await self.bot.ban_chat_member(
                chat_id=self.group_id,
                user_id=user_id
            )
            return True
            
        except Exception as e:
            print(f"Kullanıcıyı gruptan çıkarma hatası: {e}")
            return False
    
    async def get_group_members(self) -> List[Dict]:
        """
        Grup üyelerini getirir
        
        Returns:
            Üye listesi
        """
        try:
            members = []
            async for member in self.bot.get_chat_members(chat_id=self.group_id):
                members.append({
                    'user_id': member.user.id,
                    'username': member.user.username,
                    'first_name': member.user.first_name,
                    'last_name': member.user.last_name,
                    'status': member.status
                })
            return members
            
        except Exception as e:
            print(f"Grup üyelerini getirme hatası: {e}")
            return []
    
    async def get_chat_member(self, user_id: int) -> Optional[ChatMember]:
        """
        Belirli bir kullanıcının grup üyeliğini getirir
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            ChatMember objesi veya None
        """
        try:
            return await self.bot.get_chat_member(
                chat_id=self.group_id,
                user_id=user_id
            )
        except Exception as e:
            print(f"Kullanıcı üyeliği getirme hatası: {e}")
            return None
    
    async def is_user_member(self, user_id: int) -> bool:
        """
        Kullanıcının grup üyesi olup olmadığını kontrol eder
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Üye olup olmadığı
        """
        try:
            member = await self.get_chat_member(user_id)
            if member:
                # Aiogram 2.x'te status string olarak gelir
                return member.status in ['member', 'administrator', 'creator']
            return False
        except Exception as e:
            print(f"Kullanıcı üyelik kontrolü hatası: {e}")
            return False
    
    async def handle_banned_message(self, user_id: int, message_text: str) -> bool:
        """
        Yasaklı kelimeleri kontrol eder ve gerekirse uyarı verir
        
        Args:
            user_id: Kullanıcı ID'si
            message_text: Mesaj metni
            
        Returns:
            Yasaklı kelime bulunup bulunmadığı
        """
        # Yasaklı kelimeler listesi
        banned_words = [
            'spam', 'reklam', 'satış', 'satis', 'satılık', 'satilik',
            'kiralık', 'kiralik', 'iş', 'is', 'işçi', 'isci',
            'yardım', 'yardim', 'bağış', 'bagis', 'bağış', 'bagis'
        ]
        
        message_lower = message_text.lower()
        
        for word in banned_words:
            if word in message_lower:
                # Kullanıcıya uyarı gönder
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "⚠️ **Uyarı!**\n\n"
                            "Grup kurallarına aykırı mesaj gönderdiniz. "
                            "Lütfen grup kurallarına uyun.\n\n"
                            "❌ **Yasaklı kelime:** " + word
                        )
                    )
                except Exception as e:
                    print(f"Uyarı gönderme hatası: {e}")
                
                return True
        
        return False
    
    async def get_group_info(self) -> Dict:
        """
        Grup bilgilerini getirir
        
        Returns:
            Grup bilgileri
        """
        try:
            chat = await self.bot.get_chat(chat_id=self.group_id)
            return {
                'id': chat.id,
                'title': chat.title,
                'type': chat.type,
                'member_count': chat.member_count if hasattr(chat, 'member_count') else None,
                'description': chat.description if hasattr(chat, 'description') else None
            }
        except Exception as e:
            print(f"Grup bilgisi getirme hatası: {e}")
            return {}
    
    async def send_group_message(self, message_text: str, parse_mode: str = "HTML") -> bool:
        """
        Gruba mesaj gönderir
        
        Args:
            message_text: Mesaj metni
            parse_mode: Parse modu (HTML, Markdown)
            
        Returns:
            Başarı durumu
        """
        try:
            await self.bot.send_message(
                chat_id=self.group_id,
                text=message_text,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"Grup mesajı gönderme hatası: {e}")
            return False
    
    async def pin_message(self, message_id: int) -> bool:
        """
        Mesajı sabitler
        
        Args:
            message_id: Mesaj ID'si
            
        Returns:
            Başarı durumu
        """
        try:
            await self.bot.pin_chat_message(
                chat_id=self.group_id,
                message_id=message_id
            )
            return True
        except Exception as e:
            print(f"Mesaj sabitleme hatası: {e}")
            return False
    
    async def unpin_message(self, message_id: int) -> bool:
        """
        Mesajın sabitini kaldırır
        
        Args:
            message_id: Mesaj ID'si
            
        Returns:
            Başarı durumu
        """
        try:
            await self.bot.unpin_chat_message(
                chat_id=self.group_id,
                message_id=message_id
            )
            return True
        except Exception as e:
            print(f"Mesaj sabit kaldırma hatası: {e}")
            return False
