#!/usr/bin/env python3
"""
Bağlantı test scripti
"""

import os
from dotenv import load_dotenv
from services.database import DatabaseService
import asyncio

async def test_connection():
    """Veritabanı bağlantısını test eder"""
    print("🔍 Veritabanı bağlantısı test ediliyor...")
    
    try:
        # Environment değişkenlerini yükle
        load_dotenv()
        
        # Gerekli değişkenleri kontrol et
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Eksik environment değişkenleri: {', '.join(missing_vars)}")
            print("📝 .env dosyasını oluşturun ve gerekli değerleri ekleyin")
            return False
        
        print("✅ Environment değişkenleri mevcut")
        
        # Database service'i test et
        db = DatabaseService()
        print("✅ Database service başlatıldı")
        
        # Basit bir sorgu test et
        questions = await db.get_questions()
        print(f"✅ Sorular başarıyla getirildi: {len(questions)} adet")
        
        return True
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        print(f"Hata türü: {type(e).__name__}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    if result:
        print("\n🎉 Test başarılı! Proje çalışmaya hazır.")
    else:
        print("\n💥 Test başarısız! Lütfen hataları düzeltin.")
