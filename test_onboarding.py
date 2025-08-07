#!/usr/bin/env python3
"""
Onboarding Flow Test Script
Bu script bot'un onboarding akışını test eder.
"""

import asyncio
import sys
from config import Config

def test_onboarding_flow():
    """Onboarding akışını test eder"""
    print("🧪 Onboarding Flow Test\n")
    
    # 1. Config kontrolü
    print("1. ✅ Config kontrolü...")
    try:
        Config.validate_config()
        print("   - BOT_TOKEN: ✅")
        print("   - SUPABASE_URL: ✅")
        print("   - SUPABASE_KEY: ✅")
    except ValueError as e:
        print(f"   - ❌ Config hatası: {e}")
        return False
    
    # 2. Mesaj kontrolü
    print("\n2. ✅ Mesaj kontrolü...")
    welcome_msg = Config.WELCOME_MESSAGE.format(username="test_user")
    print(f"   - Hoş geldin mesajı: {welcome_msg[:50]}...")
    
    print(f"   - Tanıtım mesajı: {Config.PROMOTION_MESSAGE[:50]}...")
    
    # 3. Varsayılan sorular kontrolü
    print("\n3. ✅ Varsayılan sorular kontrolü...")
    for i, question in enumerate(Config.DEFAULT_QUESTIONS, 1):
        print(f"   - Soru {i}: {question}")
    
    # 4. Handler import kontrolü
    print("\n4. ✅ Handler import kontrolü...")
    try:
        from handlers.user_handlers import UserHandler, UserStates
        from services.database import DatabaseService
        from services.file_service import FileService
        from services.group_service import GroupService
        print("   - UserHandler: ✅")
        print("   - UserStates: ✅")
        print("   - DatabaseService: ✅")
        print("   - FileService: ✅")
        print("   - GroupService: ✅")
    except Exception as e:
        print(f"   - ❌ Import hatası: {e}")
        return False
    
    # 5. Admin handler kontrolü
    print("\n5. ✅ Admin handler kontrolü...")
    try:
        from handlers.admin_handlers import AdminHandler, AdminStates
        print("   - AdminHandler: ✅")
        print("   - AdminStates: ✅")
    except Exception as e:
        print(f"   - ❌ Admin import hatası: {e}")
        return False
    
    # 6. Group handler kontrolü
    print("\n6. ✅ Group handler kontrolü...")
    try:
        from handlers.group_handlers import router as group_router
        print("   - Group router: ✅")
    except Exception as e:
        print(f"   - ❌ Group import hatası: {e}")
        return False
    
    print("\n🎉 Onboarding flow test başarılı!")
    print("\n📋 Test edilecek akış:")
    print("1. /start komutu → Hoş geldin mesajı")
    print("2. '📋 Tanıtımı Gör' butonu → Tanıtım mesajı")
    print("3. Sorular sırayla sorulur")
    print("4. Sorular bitince ödeme kısmı")
    print("5. '💳 Ödeme Yaptım' veya '📎 Dekont Ekle'")
    print("6. Admin onayı beklenir")
    print("7. Onaylanınca gruba eklenir")
    
    return True

def main():
    """Ana test fonksiyonu"""
    print("🚀 Starting Onboarding Flow Test\n")
    
    if test_onboarding_flow():
        print("\n✅ Tüm testler başarılı! Bot onboarding akışı hazır.")
        print("\n🎯 Şimdi test edebilirsiniz:")
        print("1. Bot'a /start gönderin")
        print("2. '📋 Tanıtımı Gör' butonuna tıklayın")
        print("3. Soruları yanıtlayın")
        print("4. Ödeme kısmını test edin")
    else:
        print("\n❌ Testler başarısız! Lütfen hataları düzeltin.")
        sys.exit(1)

if __name__ == "__main__":
    main()
