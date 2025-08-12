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
        Dosyayı kaydeder ve URL'ini döner
        
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
            file_path = os.path.join(self.upload_dir, unique_name)
            print(f"DEBUG FileService: Dosya yolu: {file_path}")
            
            # Dosyayı kaydet
            print(f"DEBUG FileService: Dosya kaydediliyor...")
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            print(f"DEBUG FileService: Dosya kaydedildi")
            
            # Dosya URL'ini döner (gerçek uygulamada CDN URL'i olacak)
            file_url = f"/uploads/{unique_name}"
            print(f"DEBUG FileService: file_url döndürülüyor: {file_url}")
            return file_url
            
        except Exception as e:
            print(f"DEBUG FileService: Exception yakalandı: {e}")
            print(f"DEBUG FileService: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Dosyayı siler
        
        Args:
            file_url: Dosya URL'i
            
        Returns:
            Başarı durumu
        """
        try:
            # URL'den dosya yolunu çıkar
            file_name = file_url.split('/')[-1]
            file_path = os.path.join(self.upload_dir, file_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            print(f"Dosya silme hatası: {e}")
            return False
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """
        Dosya bilgilerini getirir
        
        Args:
            file_url: Dosya URL'i
            
        Returns:
            Dosya bilgileri veya None
        """
        try:
            file_name = file_url.split('/')[-1]
            file_path = os.path.join(self.upload_dir, file_name)
            
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                return {
                    'name': file_name,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime)
                }
            return None
            
        except Exception as e:
            print(f"Dosya bilgisi getirme hatası: {e}")
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
