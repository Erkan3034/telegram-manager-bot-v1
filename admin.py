from passlib.hash import bcrypt 

try:
    hashed = bcrypt.hash('Qwerty10082025')
    print("Hash:", hashed)
except Exception as e:
    print("Hata oluştu:", e)