"""
Flask Web Uygulaması
Bu dosya web arayüzü için Flask uygulamasını içerir.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session
from flask_cors import CORS
import os
from datetime import datetime
import asyncio
from config import Config
import json
from services.database import DatabaseService
from passlib.hash import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
CORS(app)

def get_db():
    """Database service instance'ını döndürür"""
    from services.database import DatabaseService
    return DatabaseService()

def run_async(coro):
    """Async fonksiyonları çalıştırmak için yardımcı fonksiyon"""
    return asyncio.run(coro)

async def _invite_user_async(user_id: int):
    """Kullanıcıya onay mesajı ve davet linki göndermek için async yardımcı."""
    from aiogram import Bot
    from services.group_service import GroupService
    bot = Bot(token=Config.BOT_TOKEN)
    try:
        group_service = GroupService(bot)
        await group_service.add_user_to_group(user_id)
    finally:
        await bot.session.close()

def invite_user(user_id: int):
    """Sync wrapper to invite a user to the group and notify them."""
    return run_async(_invite_user_async(user_id))

async def _apply_commands_async():
    """bot_settings içindeki komutları Telegram'a set eder."""
    from aiogram import Bot
    from services.database import DatabaseService
    bot = Bot(token=Config.BOT_TOKEN)
    try:
        db = DatabaseService()
        settings = await db.get_bot_settings()
        commands_json = settings.get('commands') if settings else None
        commands = []
        if commands_json:
            try:
                data = json.loads(commands_json)
                from aiogram.types import BotCommand
                for item in data:
                    cmd = (item.get('command') or '').strip().lstrip('/')
                    desc = (item.get('description') or '').strip()
                    if cmd and desc:
                        commands.append(BotCommand(command=cmd, description=desc))
            except Exception:
                commands = []
        if not commands:
            from aiogram.types import BotCommand
            commands = [
                BotCommand(command='start', description='Botu başlat'),
                BotCommand(command='admin', description='Admin paneli'),
                BotCommand(command='help', description='Yardım'),
            ]
        await bot.set_my_commands(commands)
        return True
    finally:
        await bot.session.close()

def apply_commands():
    return run_async(_apply_commands_async())

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """Admin paneli"""
    if not session.get('admin_authenticated'):
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/login')
def login_page():
    if session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    # Basit bir login formu (template kullanmadan minimal)
    return '''
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Admin Giriş</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="bg-light">
    <div class="container py-5"><div class="row justify-content-center"><div class="col-md-4">
    <div class="card shadow-sm">
    <div class="card-header"><strong>Admin Giriş</strong></div>
    <div class="card-body">
      <div class="mb-3">
        <label class="form-label">E-posta</label>
        <input id="email" type="email" class="form-control" placeholder="admin@example.com"/>
      </div>
      <div class="mb-3">
        <label class="form-label">Şifre</label>
        <input id="password" type="password" class="form-control" placeholder="******"/>
      </div>
      <button class="btn btn-primary w-100" onclick="login()">Giriş Yap</button>
      <div id="msg" class="text-danger small mt-2"></div>
    </div></div></div></div></div>
    <script>
    async function login(){
      const res = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('email').value,password:document.getElementById('password').value})});
      const data = await res.json();
      if(res.ok && data.success){ window.location = '/admin'; }
      else{ document.getElementById('msg').innerText = data.error || 'Giriş başarısız'; }
    }
    </script>
    </body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')
    if not email or not password:
        return jsonify({'error':'E-posta ve şifre zorunludur'}), 400
    db = DatabaseService()
    admin = run_async(db.get_admin_by_email(email))
    if not admin:
        return jsonify({'error':'Admin bulunamadı'}), 401
    # Basit hash kontrolü (prod için bcrypt/argon2 önerilir)
    if not bcrypt.verify(password, (admin.get('password_hash') or '')):
        return jsonify({'error':'Şifre hatalı'}), 401
    session['admin_authenticated'] = True
    session['admin_email'] = email
    session.permanent = True
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    """İstatistikleri getirir"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        total_users = len(run_async(db.get_all_users()))
        total_payments = len(run_async(db.get_all_payments()))
        pending_payments = len(run_async(db.get_pending_payments()))
        total_members = len(run_async(db.get_group_members(Config.GROUP_ID)))
        
        return jsonify({
            'total_users': total_users,
            'total_payments': total_payments,
            'pending_payments': pending_payments,
            'total_members': total_members
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions')
def get_questions():
    """Soruları getirir"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        questions = run_async(db.get_questions())
        return jsonify(questions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def add_question():
    """Yeni soru ekler"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        data = request.get_json()
        question_text = data.get('question_text')
        
        if not question_text:
            return jsonify({'error': 'Soru metni gerekli'}), 400
        
        question = run_async(db.add_question(question_text))
        return jsonify(question)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Soruyu siler"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        success = run_async(db.delete_question(question_id))
        if success:
            return jsonify({'message': 'Soru silindi'})
        else:
            return jsonify({'error': 'Soru silinemedi'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments')
def get_payments():
    """Ödemeleri getirir"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        payments = run_async(db.get_pending_payments())
        return jsonify(payments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipts')
def get_receipts():
    """Dekontları getirir"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        receipts = run_async(db.get_pending_receipts())
        return jsonify(receipts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>/approve', methods=['POST'])
def approve_payment(payment_id):
    """Ödemeyi onaylar ve kullanıcıyı davet eder"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        success = run_async(db.update_payment_status(payment_id, 'approved'))
        if success:
            payment = run_async(db.get_payment(payment_id))
            if payment and payment.get('user_id'):
                invite_user(payment['user_id'])
            return jsonify({'message': 'Ödeme onaylandı ve kullanıcıya davet gönderildi'})
        else:
            return jsonify({'error': 'Ödeme onaylanamadı'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>/reject', methods=['POST'])
def reject_payment(payment_id):
    """Ödemeyi reddeder"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        success = run_async(db.update_payment_status(payment_id, 'rejected'))
        if success:
            return jsonify({'message': 'Ödeme reddedildi'})
        else:
            return jsonify({'error': 'Ödeme reddedilemedi'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipts/<int:receipt_id>/approve', methods=['POST'])
def approve_receipt(receipt_id):
    """Dekontu onaylar ve kullanıcıyı davet eder"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        success = run_async(db.update_receipt_status(receipt_id, 'approved'))
        if success:
            receipt = run_async(db.get_receipt(receipt_id))
            if receipt and receipt.get('user_id'):
                invite_user(receipt['user_id'])
            return jsonify({'message': 'Dekont onaylandı ve kullanıcıya davet gönderildi'})
        else:
            return jsonify({'error': 'Dekont onaylanamadı'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipts/<int:receipt_id>/reject', methods=['POST'])
def reject_receipt(receipt_id):
    """Dekontu reddeder"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        success = run_async(db.update_receipt_status(receipt_id, 'rejected'))
        if success:
            return jsonify({'message': 'Dekont reddedildi'})
        else:
            return jsonify({'error': 'Dekont reddedilemedi'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/members')
def get_members():
    """Grup üyelerini getirir"""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        members = run_async(db.get_group_members(Config.GROUP_ID))
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/invited')
def get_invited_members():
    """Davet gönderilmiş (group_members kaydı olan) kullanıcıları listeler."""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        db = get_db()
        members = run_async(db.get_group_members(Config.GROUP_ID))
        # invited/active ayrımı varsa status ile filtreleyebiliriz; şu an tamamını dönüyoruz
        return jsonify(members)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot-settings', methods=['GET', 'POST'])
def bot_settings():
    """Start/help mesajlarını görüntüle/güncelle."""
    db = get_db()
    if request.method == 'GET':
        if not session.get('admin_authenticated'):
            return redirect(url_for('login_page'))
        settings = run_async(db.get_bot_settings())
        # Config'teki mevcut değerlere fallback
        settings.setdefault('group_id', Config.GROUP_ID)
        settings.setdefault('shopier_payment_url', Config.SHOPIER_PAYMENT_URL)
        return jsonify(settings)
    if not session.get('admin_authenticated'):
        return jsonify({'error':'unauthorized'}), 401
    data = request.get_json() or {}
    ok = run_async(db.update_bot_settings(
        start_message=data.get('start_message'),
        help_message=data.get('help_message'),
        intro_message=data.get('intro_message'),
        promotion_message=data.get('promotion_message'),
        payment_message=data.get('payment_message'),
        commands=data.get('commands'),
        group_id=data.get('group_id'),
        shopier_payment_url=data.get('shopier_payment_url')
    ))
    # In-memory Config güncellemesi (process çalıştığı sürece etkili olur)
    try:
        if 'group_id' in data and str(data['group_id']).strip():
            from config import Config as _C
            _C.GROUP_ID = int(str(data['group_id']).strip())
        if 'shopier_payment_url' in data and data['shopier_payment_url']:
            from config import Config as _C
            _C.SHOPIER_PAYMENT_URL = data['shopier_payment_url']
    except Exception:
        pass
    return jsonify({'success': ok})

@app.route('/api/bot-settings/apply-commands', methods=['POST'])
def bot_apply_commands():
    """Komut listesini anında Telegram'a uygular."""
    try:
        if not session.get('admin_authenticated'):
            return jsonify({'error':'unauthorized'}), 401
        ok = apply_commands()
        return jsonify({'success': ok})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Yüklenen dosyaları serve eder"""
    return send_from_directory('uploads', filename)

@app.errorhandler(404)
def not_found(error):
    """404 hatası"""
    return jsonify({'error': 'Sayfa bulunamadı'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 hatası"""
    return jsonify({'error': 'Sunucu hatası'}), 500

if __name__ == '__main__':
    app.run(debug=Config.FLASK_ENV == 'development', host='0.0.0.0', port=5000)
