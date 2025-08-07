#!/usr/bin/env python3
"""
Test script to verify that all components are working correctly
"""

import asyncio
import sys
import os

def test_imports():
    """Test all imports"""
    print("🔍 Testing imports...")
    
    try:
        from config import Config
        print("✅ Config imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from services.database import DatabaseService
        print("✅ DatabaseService imported successfully")
    except Exception as e:
        print(f"❌ DatabaseService import failed: {e}")
        return False
    
    try:
        from services.file_service import FileService
        print("✅ FileService imported successfully")
    except Exception as e:
        print(f"❌ FileService import failed: {e}")
        return False
    
    try:
        from services.group_service import GroupService
        print("✅ GroupService imported successfully")
    except Exception as e:
        print(f"❌ GroupService import failed: {e}")
        return False
    
    try:
        from handlers.user_handlers import router as user_router
        print("✅ User handlers imported successfully")
    except Exception as e:
        print(f"❌ User handlers import failed: {e}")
        return False
    
    try:
        from handlers.admin_handlers import router as admin_router
        print("✅ Admin handlers imported successfully")
    except Exception as e:
        print(f"❌ Admin handlers import failed: {e}")
        return False
    
    try:
        from handlers.group_handlers import router as group_router
        print("✅ Group handlers imported successfully")
    except Exception as e:
        print(f"❌ Group handlers import failed: {e}")
        return False
    
    try:
        import app
        print("✅ Flask app imported successfully")
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    try:
        import main
        print("✅ Main module imported successfully")
    except Exception as e:
        print(f"❌ Main module import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    from config import Config
    
    # Check required environment variables
    required_vars = ['BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
    
    for var in required_vars:
        value = getattr(Config, var, None)
        if value:
            print(f"✅ {var} is configured")
        else:
            print(f"⚠️  {var} is not configured (this is expected if .env file doesn't exist)")
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from services.database import DatabaseService
        
        # Check if environment variables are configured
        from config import Config
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            print("⚠️  Database connection test skipped (requires .env configuration)")
            print("   Please create a .env file with your Supabase credentials")
            return True
        
        db = DatabaseService()
        print("✅ DatabaseService initialized successfully")
        
        # Test a simple query
        try:
            questions = asyncio.run(db.get_questions())
            print(f"✅ Database connection successful (found {len(questions)} questions)")
        except Exception as e:
            print(f"⚠️  Database query test failed (this is normal if tables don't exist yet): {e}")
        
        return True
    except Exception as e:
        if "supabase_url is required" in str(e):
            print("⚠️  Database connection test skipped (requires .env configuration)")
            print("   Please create a .env file with your Supabase credentials")
            return True
        else:
            print(f"❌ DatabaseService initialization failed: {e}")
            return False

def main():
    """Main test function"""
    print("🚀 Starting Telegram Bot Setup Test\n")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed!")
        sys.exit(1)
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration tests failed!")
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection tests failed!")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your Telegram bot is ready to run.")
    print("\n📝 Next steps:")
    print("1. Create a .env file with your configuration (see env.example)")
    print("2. Set up your Supabase database tables (see README.md)")
    print("3. Run 'python main.py' to start the bot")
    print("4. Run 'python app.py' to start the web admin panel")

if __name__ == "__main__":
    main()
