"""
DB Write Throttling Service
Aynı kullanıcıdan çok kısa sürede gelen mesajlarda DB write'ı engeller
Redis olmadan in-memory throttling
"""

from typing import Dict, Set
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class ThrottleService:
    """DB write throttling servisi"""
    
    def __init__(self):
        # user_id -> [timestamp1, timestamp2, ...]
        self._user_write_timestamps: Dict[int, list] = defaultdict(list)
        # user_id -> {operation: timestamp}
        self._user_operation_timestamps: Dict[int, Dict[str, datetime]] = defaultdict(dict)
        self._lock = threading.Lock()
        
        # Throttle ayarları
        self.WRITE_WINDOW_SECONDS = 5  # 5 saniye içinde
        self.MAX_WRITES_PER_WINDOW = 1  # Maksimum 1 write
        
        # Operation-specific throttle (daha uzun süre)
        self.OPERATION_THROTTLE_SECONDS = {
            'create_user': 60,  # 60 saniyede bir kullanıcı oluşturma
            'save_answer': 2,   # 2 saniyede bir cevap kaydetme
            'save_receipt': 10, # 10 saniyede bir dekont kaydetme
            'create_payment': 30, # 30 saniyede bir ödeme kaydı
        }
    
    def should_throttle(self, user_id: int, operation: str = None) -> bool:
        """
        Kullanıcı için throttle kontrolü yapar
        
        Args:
            user_id: Kullanıcı ID'si
            operation: İşlem tipi (opsiyonel, operation-specific throttle için)
            
        Returns:
            True: Throttle uygulanmalı (DB write yapma)
            False: DB write yapılabilir
        """
        with self._lock:
            now = datetime.now()
            
            # Operation-specific throttle kontrolü
            if operation and operation in self.OPERATION_THROTTLE_SECONDS:
                last_timestamp = self._user_operation_timestamps[user_id].get(operation)
                if last_timestamp:
                    elapsed = (now - last_timestamp).total_seconds()
                    if elapsed < self.OPERATION_THROTTLE_SECONDS[operation]:
                        return True  # Throttle uygula
                # Throttle yok, timestamp'i güncelle
                self._user_operation_timestamps[user_id][operation] = now
            
            # Genel write throttle kontrolü
            timestamps = self._user_write_timestamps[user_id]
            # Eski kayıtları temizle
            timestamps[:] = [
                ts for ts in timestamps
                if (now - ts).total_seconds() < self.WRITE_WINDOW_SECONDS
            ]
            
            # Throttle kontrolü
            if len(timestamps) >= self.MAX_WRITES_PER_WINDOW:
                return True  # Throttle uygula
            
            # Write yapılabilir, timestamp ekle
            timestamps.append(now)
            return False
    
    def record_write(self, user_id: int, operation: str = None) -> None:
        """
        DB write'ı kaydeder (manuel kayıt için)
        
        Args:
            user_id: Kullanıcı ID'si
            operation: İşlem tipi
        """
        with self._lock:
            now = datetime.now()
            self._user_write_timestamps[user_id].append(now)
            if operation:
                self._user_operation_timestamps[user_id][operation] = now
    
    def cleanup_old_records(self) -> None:
        """Eski throttle kayıtlarını temizler"""
        with self._lock:
            now = datetime.now()
            
            # Genel write timestamps temizleme
            for user_id in list(self._user_write_timestamps.keys()):
                timestamps = self._user_write_timestamps[user_id]
                timestamps[:] = [
                    ts for ts in timestamps
                    if (now - ts).total_seconds() < self.WRITE_WINDOW_SECONDS * 2
                ]
                if not timestamps:
                    del self._user_write_timestamps[user_id]
            
            # Operation timestamps temizleme
            max_throttle = max(self.OPERATION_THROTTLE_SECONDS.values()) if self.OPERATION_THROTTLE_SECONDS else 60
            for user_id in list(self._user_operation_timestamps.keys()):
                operations = self._user_operation_timestamps[user_id]
                operations_to_remove = []
                for op, timestamp in operations.items():
                    if (now - timestamp).total_seconds() > max_throttle * 2:
                        operations_to_remove.append(op)
                for op in operations_to_remove:
                    del operations[op]
                if not operations:
                    del self._user_operation_timestamps[user_id]


# Global throttle instance
_throttle_service = ThrottleService()

def get_throttle() -> ThrottleService:
    """Global throttle instance'ını döndürür"""
    return _throttle_service

