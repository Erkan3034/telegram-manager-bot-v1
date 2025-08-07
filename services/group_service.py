"""
Telegram Grup Yönetimi Servisi
Bu dosya Telegram gruplarındaki işlemleri yönetir.
"""

from typing import List, Optional, Dict
from aiogram import Bot
from aiogram.types import ChatMember
from aiogram.enums import ChatMemberStatus
from config import Config

class GroupService:
    """Telegram grup yönetimi servisi"""
    
    def __init__(self, bot: Bot):
        """Grup servisini başlatır"""
        self.bot = bot
        self.group_id = Config.GROUP_ID
    
    async def add_user_to_group(self, user_id: int) -> bool:
        """
        Kullanıcıyı gruba ekler
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Başarı durumu
        """
        try:
            # Kullanıcıyı gruba davet et
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=self.group_id,
                member_limit=1
            )
            
            # Kullanıcıya davet linkini gönder
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Tebrikler! Ödeme onaylandı.\n\nGrubumuza katılmak için aşağıdaki linke tıklayın:\n{invite_link.invite_link}"
            )
            
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
                    'status': member.status.value
                })
            return members
            
        except Exception as e:
            print(f"Grup üyelerini getirme hatası: {e}")
            return []
    
    async def check_user_in_group(self, user_id: int) -> bool:
        """
        Kullanıcının grupta olup olmadığını kontrol eder
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Grupta olup olmadığı
        """
        try:
            member = await self.bot.get_chat_member(
                chat_id=self.group_id,
                user_id=user_id
            )
            return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            
        except Exception as e:
            print(f"Kullanıcı grup kontrolü hatası: {e}")
            return False
    
    async def warn_user(self, user_id: int, message: str) -> bool:
        """
        Kullanıcıyı uyarır
        
        Args:
            user_id: Kullanıcı ID'si
            message: Uyarı mesajı
            
        Returns:
            Başarı durumu
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=f"⚠️ **Uyarı:** {message}"
            )
            return True
            
        except Exception as e:
            print(f"Kullanıcı uyarma hatası: {e}")
            return False
    
    async def check_banned_words(self, message_text: str) -> List[str]:
        """
        Mesajda yasaklı kelimeleri kontrol eder
        
        Args:
            message_text: Kontrol edilecek mesaj
            
        Returns:
            Bulunan yasaklı kelimeler listesi
        """
        found_words = []
        message_lower = message_text.lower()
        
        for word in Config.BANNED_WORDS:
            if word.lower() in message_lower:
                found_words.append(word)
        
        return found_words
    
    async def handle_banned_message(self, user_id: int, message_text: str) -> bool:
        """
        Yasaklı kelime içeren mesajı işler
        
        Args:
            user_id: Kullanıcı ID'si
            message_text: Mesaj metni
            
        Returns:
            Başarı durumu
        """
        try:
            banned_words = await self.check_banned_words(message_text)
            
            if banned_words:
                warning_message = f"⚠️ Mesajınızda yasaklı kelimeler bulundu: {', '.join(banned_words)}\n\nLütfen daha saygılı bir dil kullanın."
                
                await self.warn_user(user_id, warning_message)
                
                # Admin'e bildir
                await self.notify_admin_banned_message(user_id, message_text, banned_words)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Yasaklı mesaj işleme hatası: {e}")
            return False
    
    async def notify_admin_banned_message(self, user_id: int, message_text: str, banned_words: List[str]) -> bool:
        """
        Admin'e yasaklı mesaj hakkında bildirim gönderir
        
        Args:
            user_id: Kullanıcı ID'si
            message_text: Mesaj metni
            banned_words: Yasaklı kelimeler
            
        Returns:
            Başarı durumu
        """
        try:
            for admin_id in Config.ADMIN_IDS:
                notification = f"""
🚨 **Yasaklı Mesaj Bildirimi**

👤 **Kullanıcı:** {user_id}
📝 **Mesaj:** {message_text[:100]}...
🚫 **Yasaklı Kelimeler:** {', '.join(banned_words)}

⚠️ Kullanıcı uyarıldı.
                """
                
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=notification
                )
            
            return True
            
        except Exception as e:
            print(f"Admin bildirimi hatası: {e}")
            return False
    
    async def get_group_info(self) -> Optional[Dict]:
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
                'username': chat.username,
                'member_count': chat.member_count,
                'description': chat.description
            }
            
        except Exception as e:
            print(f"Grup bilgisi getirme hatası: {e}")
            return None
