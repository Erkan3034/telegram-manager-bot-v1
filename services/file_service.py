"""
Dosya Yönetimi Servisi
Bu dosya dosya yükleme, indirme ve yönetimi işlemlerini yapar.
"""

import os
import aiofiles
import uuid
from typing import Optional, Tuple
from datetime import datetime
from config import Config
from services.database import DatabaseService


class FileService:
    """Dosya yönetimi servisi"""
    
    def __init__(self):
        """Dosya servisini başlatır"""
        self.upload_dir = "uploads"
        self.ensure_upload_dir()
    
    def ensure_upload_dir(self):
        """Upload dizininin varlığını kontrol eder ve oluşturur"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    async def save_file(self, file_data: bytes, file_name: str, user_id: int) -> Optional[str]:
        """
        Dosyayı Supabase Storage'a kaydeder ve URL'ini döner
        
        Args:
            file_data: Dosya içeriği
            file_name: Dosya adı
            user_id: Kullanıcı ID'si
            
        Returns:
            Dosya URL'i veya None
        """
        try:
            print(f"DEBUG FileService: save_file çağrıldı - file_name: {file_name}, user_id: {user_id}, data_size: {len(file_data) if file_data else 'None'}")
            
            # Dosya uzantısını kontrol et
            file_ext = os.path.splitext(file_name)[1].lower()
            print(f"DEBUG FileService: file_ext: {file_ext}")
            if file_ext not in Config.ALLOWED_EXTENSIONS:
                print(f"DEBUG FileService: Desteklenmeyen dosya türü: {file_ext}")
                raise ValueError(f"Desteklenmeyen dosya türü: {file_ext}")
            
            # Dosya boyutunu kontrol et
            if len(file_data) > Config.MAX_FILE_SIZE:
                print(f"DEBUG FileService: Dosya boyutu çok büyük: {len(file_data)} bytes")
                raise ValueError(f"Dosya boyutu çok büyük: {len(file_data)} bytes")
            
            # Benzersiz dosya adı oluştur
            unique_name = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
            print(f"DEBUG FileService: Benzersiz dosya adı: {unique_name}")
            
            # Supabase Storage'a yükle
            print(f"DEBUG FileService: Supabase Storage'a yükleniyor...")
            db_service = DatabaseService()
            
            # Storage bucket'a dosyayı yükle
            storage_response = db_service.supabase.storage.from_('receipts').upload(
                path=unique_name,
                file=file_data,
                file_options={'content-type': self._get_content_type(file_ext)}
            )
            
            if not storage_response:
                print(f"DEBUG FileService: Supabase Storage yükleme başarısız")
                raise Exception("Supabase Storage yükleme başarısız")
            
            print(f"DEBUG FileService: Supabase Storage'a yüklendi")
            
            # Public URL oluştur
            file_url = db_service.supabase.storage.from_('receipts').get_public_url(unique_name)
            print(f"DEBUG FileService: Public URL: {file_url}")
            
            return file_url
            
        except Exception as e:
            print(f"DEBUG FileService: Exception yakalandı: {e}")
            print(f"DEBUG FileService: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Local dosya sistemi
            print(f"DEBUG FileService: Fallback - Local dosya sistemi deneniyor...")
            try:
                return await self._save_file_local(file_data, file_name, user_id)
            except Exception as fallback_error:
                print(f"DEBUG FileService: Fallback da başarısız: {fallback_error}")
                return None
    
    def _get_content_type(self, file_ext: str) -> str:
        """Dosya uzantısına göre content-type döner"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.pdf': 'application/pdf'
        }
        return content_types.get(file_ext, 'application/octet-stream')
    
    async def _save_file_local(self, file_data: bytes, file_name: str, user_id: int) -> Optional[str]:
        """Fallback: Dosyayı local dosya sistemine kaydeder"""
        try:
            print(f"DEBUG FileService: Local fallback - Dosya kaydediliyor...")
            
            # Benzersiz dosya adı oluştur
            unique_name = f"{user_id}_{uuid.uuid4().hex}{os.path.splitext(file_name)[1].lower()}"
            file_path = os.path.join(self.upload_dir, unique_name)
            
            # Klasörü oluştur
            self.ensure_upload_dir()
            
            # Dosyayı kaydet
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            print(f"DEBUG FileService: Local fallback - Dosya kaydedildi: {file_path}")
            
            # Local URL döner
            file_url = f"/uploads/{unique_name}"
            return file_url
            
        except Exception as e:
            print(f"DEBUG FileService: Local fallback hatası: {e}")
            return None
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Dosyayı Supabase Storage'dan siler
        
        Args:
            file_url: Dosya URL'i
            
        Returns:
            Başarı durumu
        """
        try:
            # URL'den dosya adını çıkar
            file_name = file_url.split('/')[-1]
            print(f"DEBUG FileService: Dosya siliniyor: {file_name}")
            
            # Supabase Storage'dan sil
            db_service = DatabaseService()
            storage_response = db_service.supabase.storage.from_('receipts').remove([file_name])
            
            if storage_response:
                print(f"DEBUG FileService: Supabase Storage'dan silindi")
                return True
            else:
                print(f"DEBUG FileService: Supabase Storage silme başarısız")
                return False
                
        except Exception as e:
            print(f"DEBUG FileService: Supabase Storage silme hatası: {e}")
            
            # Fallback: Local dosya sistemi
            try:
                file_path = os.path.join(self.upload_dir, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"DEBUG FileService: Local fallback - Dosya silindi")
                    return True
            except Exception as fallback_error:
                print(f"DEBUG FileService: Local fallback silme hatası: {fallback_error}")
            
            return False
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """
        Dosya bilgilerini Supabase Storage'dan getirir
        
        Args:
            file_url: Dosya URL'i
            
        Returns:
            Dosya bilgileri veya None
        """
        try:
            file_name = file_url.split('/')[-1]
            print(f"DEBUG FileService: Dosya bilgileri alınıyor: {file_name}")
            
            # Supabase Storage'dan dosya bilgilerini al
            db_service = DatabaseService()
            
            try:
                # Storage'dan dosya listesini al
                files = db_service.supabase.storage.from_('receipts').list()
                
                # Dosyayı bul
                target_file = None
                for file_info in files:
                    if file_info.name == file_name:
                        target_file = file_info
                        break
                
                if target_file:
                    return {
                        'name': target_file.name,
                        'size': target_file.metadata.get('size', 0),
                        'created_at': datetime.now(),  # Supabase'de creation time yok
                        'modified_at': datetime.now()
                    }
                else:
                    print(f"DEBUG FileService: Dosya Supabase Storage'da bulunamadı")
                    return None
                    
            except Exception as storage_error:
                print(f"DEBUG FileService: Supabase Storage bilgi alma hatası: {storage_error}")
                return None
            
        except Exception as e:
            print(f"DEBUG FileService: Dosya bilgisi getirme hatası: {e}")
            return None
    
    def validate_file(self, file_name: str, file_size: int) -> Tuple[bool, str]:
        """
        Dosya geçerliliğini kontrol eder
        
        Args:
            file_name: Dosya adı
            file_size: Dosya boyutu
            
        Returns:
            (geçerli_mi, hata_mesajı)
        """
        # Dosya uzantısını kontrol et
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return False, f"Desteklenmeyen dosya türü: {file_ext}"
        
        # Dosya boyutunu kontrol et
        if file_size > Config.MAX_FILE_SIZE:
            return False, f"Dosya boyutu çok büyük: {file_size} bytes"
        
        return True, ""
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Eski dosyaları temizler
        
        Args:
            days: Kaç günden eski dosyaların silineceği
            
        Returns:
            Silinen dosya sayısı
        """
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            deleted_count = 0
            for file_name in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, file_name)
                if os.path.isfile(file_path):
                    file_time = os.path.getctime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            print(f"Dosya temizleme hatası: {e}")
            return 0
