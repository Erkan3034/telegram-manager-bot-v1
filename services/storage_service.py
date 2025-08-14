"""
Supabase Storage Servisi
Bu dosya Supabase Storage ile dosya yükleme işlemlerini yönetir.
"""

import os
import uuid
from typing import Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
from config import Config


class StorageService:
    """Supabase Storage servisi"""
    
    def __init__(self):
        """Storage servisini başlatır"""
        try:
            self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            self.bucket_name = "receipts"
            self.project_id = self._extract_project_id(Config.SUPABASE_URL)
        except Exception as e:
            print(f"Supabase Storage client initialization error: {e}")
            raise e
    
    def _extract_project_id(self, supabase_url: str) -> str:
        """Supabase URL'den project ID'yi çıkarır"""
        try:
            # https://<project-id>.supabase.co formatından project ID'yi al
            parts = supabase_url.split('//')
            if len(parts) > 1:
                project_part = parts[1].split('.')[0]
                return project_part
            return "unknown"
        except Exception as e:
            print(f"Project ID extraction error: {e}")
            return "unknown"
    
    async def upload_file(self, file_data: bytes, file_name: str, user_id: int) -> Optional[str]:
        """
        Dosyayı Supabase Storage'a yükler
        
        Args:
            file_data: Dosya içeriği (bytes)
            file_name: Orijinal dosya adı
            user_id: Kullanıcı ID'si
            
        Returns:
            Public URL veya None
        """
        try:
            print(f"DEBUG StorageService: upload_file çağrıldı - file_name: {file_name}, user_id: {user_id}, data_size: {len(file_data) if file_data else 'None'}")
            
            # Dosya uzantısını kontrol et
            file_ext = os.path.splitext(file_name)[1].lower()
            print(f"DEBUG StorageService: file_ext: {file_ext}")
            if file_ext not in Config.ALLOWED_EXTENSIONS:
                print(f"DEBUG StorageService: Desteklenmeyen dosya türü: {file_ext}")
                raise ValueError(f"Desteklenmeyen dosya türü: {file_ext}")
            
            # Dosya boyutunu kontrol et
            if len(file_data) > Config.MAX_FILE_SIZE:
                print(f"DEBUG StorageService: Dosya boyutu çok büyük: {len(file_data)} bytes")
                raise ValueError(f"Dosya boyutu çok büyük: {len(file_data)} bytes")
            
            # Benzersiz dosya adı oluştur: user_id/timestamp_uuid.ext
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            unique_name = f"{user_id}/{timestamp}_{unique_id}{file_ext}"
            
            print(f"DEBUG StorageService: Benzersiz dosya adı: {unique_name}")
            
            # Supabase Storage'a yükle
            print(f"DEBUG StorageService: Dosya Supabase Storage'a yükleniyor...")
            
            # Storage bucket'a dosyayı yükle
            result = self.supabase.storage.from_(self.bucket_name).upload(
                path=unique_name,
                file=file_data,
                file_options={"content-type": self._get_content_type(file_ext)}
            )
            
            print(f"DEBUG StorageService: Supabase upload sonucu: {result}")
            
            # Public URL oluştur
            public_url = f"https://{self.project_id}.supabase.co/storage/v1/object/public/{self.bucket_name}/{unique_name}"
            print(f"DEBUG StorageService: Public URL oluşturuldu: {public_url}")
            
            return public_url
            
        except Exception as e:
            print(f"DEBUG StorageService: Exception yakalandı: {e}")
            print(f"DEBUG StorageService: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_content_type(self, file_ext: str) -> str:
        """Dosya uzantısına göre content type döner"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.pdf': 'application/pdf'
        }
        return content_types.get(file_ext.lower(), 'application/octet-stream')
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Dosyayı Supabase Storage'dan siler
        
        Args:
            file_url: Dosya URL'i
            
        Returns:
            Başarı durumu
        """
        try:
            # URL'den dosya yolunu çıkar
            # https://<project-id>.supabase.co/storage/v1/object/public/receipts/user_id/filename.ext
            parts = file_url.split(f"/{self.bucket_name}/")
            if len(parts) > 1:
                file_path = parts[1]
                
                # Storage'dan dosyayı sil
                result = self.supabase.storage.from_(self.bucket_name).remove([file_path])
                print(f"DEBUG StorageService: Dosya silindi: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Storage dosya silme hatası: {e}")
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
            # URL'den dosya yolunu çıkar
            parts = file_url.split(f"/{self.bucket_name}/")
            if len(parts) > 1:
                file_path = parts[1]
                
                # Storage'dan dosya bilgilerini al
                result = self.supabase.storage.from_(self.bucket_name).list(path=os.path.dirname(file_path))
                
                if result:
                    for item in result:
                        if item['name'] == os.path.basename(file_path):
                            return {
                                'name': item['name'],
                                'size': item.get('metadata', {}).get('size', 0),
                                'created_at': item.get('created_at'),
                                'updated_at': item.get('updated_at')
                            }
            
            return None
            
        except Exception as e:
            print(f"Storage dosya bilgisi getirme hatası: {e}")
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
    
    async def ensure_bucket_exists(self) -> bool:
        """Storage bucket'ın varlığını kontrol eder"""
        try:
            print(f"DEBUG StorageService: Bucket kontrolü başlatılıyor...")
            
            # Bucket listesini al
            buckets = self.supabase.storage.list_buckets()
            print(f"DEBUG StorageService: Tüm bucket'lar: {buckets}")
            
            # receipts bucket'ı var mı kontrol et
            bucket_names = [bucket.name for bucket in buckets]
            print(f"DEBUG StorageService: Bucket isimleri: {bucket_names}")
            
            if self.bucket_name not in bucket_names:
                print(f"DEBUG StorageService: {self.bucket_name} bucket bulunamadı.")
                print(f"DEBUG StorageService: Lütfen Supabase Dashboard'dan manuel olarak '{self.bucket_name}' bucket'ını oluşturun.")
                print(f"DEBUG StorageService: Bucket public olmalı ve 'receipts' adında olmalı.")
                return False
            
            print(f"DEBUG StorageService: {self.bucket_name} bucket bulundu")
            return True
            
        except Exception as e:
            print(f"DEBUG StorageService: Bucket kontrol hatası: {e}")
            import traceback
            traceback.print_exc()
            return False
