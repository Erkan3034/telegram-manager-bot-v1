"""
Supabase Veritabanı İşlemleri
Bu dosya Supabase ile tüm veritabanı işlemlerini yönetir.
"""

from supabase import create_client, Client
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
from config import Config

class DatabaseService:
    """Supabase veritabanı servisi"""
    
    def __init__(self):
        """Supabase istemcisini başlatır"""
        try:
            self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        except Exception as e:
            print(f"Supabase client initialization error: {e}")
            # Try alternative initialization method
            try:
                from supabase import Client as SupabaseClient
                self.supabase = SupabaseClient(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            except Exception as e2:
                print(f"Alternative Supabase client initialization failed: {e2}")
                raise e
    
    async def create_tables(self):
        """Gerekli tabloları oluşturur (Supabase'de SQL ile oluşturulmalı)"""
        # Bu fonksiyon Supabase dashboard'unda SQL ile tablolar oluşturulduktan sonra kullanılır
        pass
    
    # Kullanıcı işlemleri
    async def create_user(self, user_id: int, username: str, first_name: str = None, last_name: str = None) -> Dict:
        """Yeni kullanıcı oluşturur"""
        try:
            user_data = {
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Kullanıcı oluşturma hatası: {e}")
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Kullanıcı bilgilerini getirir"""
        try:
            result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Kullanıcı getirme hatası: {e}")
            return None
    
    async def get_all_users(self) -> List[Dict]:
        """Tüm kullanıcıları getirir"""
        try:
            result = self.supabase.table('users').select('*').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Tüm kullanıcıları getirme hatası: {e}")
            return []
    
    async def update_user_status(self, user_id: int, status: str) -> bool:
        """Kullanıcı durumunu günceller"""
        try:
            self.supabase.table('users').update({'status': status}).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Kullanıcı durumu güncelleme hatası: {e}")
            return False
    
    # Soru işlemleri
    async def get_questions(self) -> List[Dict]:
        """Tüm soruları getirir"""
        try:
            result = self.supabase.table('questions').select('*').order('order_index').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Soruları getirme hatası: {e}")
            return []
    
    async def add_question(self, question_text: str, order_index: int = None) -> Optional[Dict]:
        """Yeni soru ekler"""
        try:
            if order_index is None:
                # Son sıraya ekle
                questions = await self.get_questions()
                order_index = len(questions) + 1
            
            question_data = {
                'question_text': question_text,
                'order_index': order_index,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('questions').insert(question_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Soru ekleme hatası: {e}")
            return None
    
    async def delete_question(self, question_id: int) -> bool:
        """Soru siler"""
        try:
            self.supabase.table('questions').delete().eq('id', question_id).execute()
            return True
        except Exception as e:
            print(f"Soru silme hatası: {e}")
            return False
    
    # Cevap işlemleri
    async def save_answer(self, user_id: int, question_id: int, answer_text: str) -> Optional[Dict]:
        """Kullanıcı cevabını kaydeder"""
        try:
            answer_data = {
                'user_id': user_id,
                'question_id': question_id,
                'answer_text': answer_text,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('answers').insert(answer_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Cevap kaydetme hatası: {e}")
            return None
    
    async def get_user_answers(self, user_id: int) -> List[Dict]:
        """Kullanıcının tüm cevaplarını getirir"""
        try:
            result = self.supabase.table('answers').select('*, questions(*)').eq('user_id', user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Kullanıcı cevaplarını getirme hatası: {e}")
            return []
    
    # Ödeme işlemleri
    async def create_payment(self, user_id: int, amount: float = 99.99) -> Optional[Dict]:
        """Yeni ödeme kaydı oluşturur"""
        try:
            payment_data = {
                'user_id': user_id,
                'amount': amount,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('payments').insert(payment_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ödeme oluşturma hatası: {e}")
            return None
    
    async def get_payment(self, payment_id: int) -> Optional[Dict]:
        """Ödeme bilgilerini getirir"""
        try:
            result = self.supabase.table('payments').select('*').eq('id', payment_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Ödeme getirme hatası: {e}")
            return None
    
    async def get_all_payments(self) -> List[Dict]:
        """Tüm ödemeleri getirir"""
        try:
            result = self.supabase.table('payments').select('*').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Tüm ödemeleri getirme hatası: {e}")
            return []
    
    async def update_payment_status(self, payment_id: int, status: str) -> bool:
        """Ödeme durumunu günceller"""
        try:
            self.supabase.table('payments').update({'status': status}).eq('id', payment_id).execute()
            return True
        except Exception as e:
            print(f"Ödeme durumu güncelleme hatası: {e}")
            return False
    
    async def get_pending_payments(self) -> List[Dict]:
        """Bekleyen ödemeleri getirir"""
        try:
            result = self.supabase.table('payments').select('*, users(*)').eq('status', 'pending').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Bekleyen ödemeleri getirme hatası: {e}")
            return []
    
    # Dekont işlemleri
    async def save_receipt(self, user_id: int, file_url: str, file_name: str) -> Optional[Dict]:
        """Dekont dosyasını kaydeder"""
        try:
            receipt_data = {
                'user_id': user_id,
                'file_url': file_url,
                'file_name': file_name,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('receipts').insert(receipt_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Dekont kaydetme hatası: {e}")
            return None
    
    async def get_receipt(self, receipt_id: int) -> Optional[Dict]:
        """Dekont bilgilerini getirir"""
        try:
            result = self.supabase.table('receipts').select('*').eq('id', receipt_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Dekont getirme hatası: {e}")
            return None
    
    async def get_pending_receipts(self) -> List[Dict]:
        """Bekleyen dekontları getirir"""
        try:
            result = self.supabase.table('receipts').select('*, users(*)').eq('status', 'pending').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Bekleyen dekontları getirme hatası: {e}")
            return []
    
    async def update_receipt_status(self, receipt_id: int, status: str) -> bool:
        """Dekont durumunu günceller"""
        try:
            self.supabase.table('receipts').update({'status': status}).eq('id', receipt_id).execute()
            return True
        except Exception as e:
            print(f"Dekont durumu güncelleme hatası: {e}")
            return False
    
    # Grup üyeliği işlemleri
    async def add_group_member(self, user_id: int, group_id: int) -> Optional[Dict]:
        """Kullanıcıyı gruba ekler"""
        try:
            member_data = {
                'user_id': user_id,
                'group_id': group_id,
                'joined_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            result = self.supabase.table('group_members').insert(member_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Grup üyesi ekleme hatası: {e}")
            return None
    
    async def get_group_members(self, group_id: int) -> List[Dict]:
        """Grup üyelerini getirir"""
        try:
            result = self.supabase.table('group_members').select('*, users(*)').eq('group_id', group_id).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Grup üyelerini getirme hatası: {e}")
            return []
    
    async def remove_group_member(self, user_id: int, group_id: int) -> bool:
        """Kullanıcıyı gruptan çıkarır"""
        try:
            self.supabase.table('group_members').delete().eq('user_id', user_id).eq('group_id', group_id).execute()
            return True
        except Exception as e:
            print(f"Grup üyesi çıkarma hatası: {e}")
            return False
