"""
Flask Web Uygulaması
Bu dosya web arayüzü için Flask uygulamasını içerir.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import asyncio
from config import Config

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

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    """Admin paneli"""
    return render_template('admin.html')

@app.route('/api/stats')
def get_stats():
    """İstatistikleri getirir"""
    try:
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
        db = get_db()
        questions = run_async(db.get_questions())
        return jsonify(questions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def add_question():
    """Yeni soru ekler"""
    try:
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
        db = get_db()
        payments = run_async(db.get_pending_payments())
        return jsonify(payments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipts')
def get_receipts():
    """Dekontları getirir"""
    try:
        db = get_db()
        receipts = run_async(db.get_pending_receipts())
        return jsonify(receipts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>/approve', methods=['POST'])
def approve_payment(payment_id):
    """Ödemeyi onaylar"""
    try:
        db = get_db()
        success = run_async(db.update_payment_status(payment_id, 'approved'))
        if success:
            return jsonify({'message': 'Ödeme onaylandı'})
        else:
            return jsonify({'error': 'Ödeme onaylanamadı'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>/reject', methods=['POST'])
def reject_payment(payment_id):
    """Ödemeyi reddeder"""
    try:
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
    """Dekontu onaylar"""
    try:
        db = get_db()
        success = run_async(db.update_receipt_status(receipt_id, 'approved'))
        if success:
            return jsonify({'message': 'Dekont onaylandı'})
        else:
            return jsonify({'error': 'Dekont onaylanamadı'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipts/<int:receipt_id>/reject', methods=['POST'])
def reject_receipt(receipt_id):
    """Dekontu reddeder"""
    try:
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
        db = get_db()
        members = run_async(db.get_group_members(Config.GROUP_ID))
        return jsonify(members)
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
