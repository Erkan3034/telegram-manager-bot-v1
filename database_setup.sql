-- Messages tablosu oluşturma
-- Bu SQL'i Supabase SQL Editor'da çalıştırın

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL CHECK (type IN ('welcome', 'question', 'payment')),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    delay DECIMAL(3,1) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mesaj türü ve sıra için index
CREATE INDEX IF NOT EXISTS idx_messages_type_order ON messages(type, order_index);

-- Aktif mesajlar için index
CREATE INDEX IF NOT EXISTS idx_messages_active ON messages(is_active) WHERE is_active = true;

-- Güncelleme zamanı için trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_messages_updated_at 
    BEFORE UPDATE ON messages 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Varsayılan mesajları ekle
INSERT INTO messages (type, title, content, order_index, delay, is_active) VALUES
('welcome', 'Hoş Geldin', '👋 Merhaba! Kompass Network''e hoş geldin.

Burası sıradan bir gelişim grubu değil.  
Burada, kendine liderlik etmek isteyen insanların oluşturduğu özel bir topluluktasın.

Sen buraya rastgele gelmedin.  
Bir şeyleri değiştirmek istediğin için buradasın.  
Hazırsan... birlikte başlayalım. 🔥', 1, 1.0, true),

('welcome', 'Kompass Network Nedir?', '📍 Peki Kompass Network nedir?

Kompass Network; Karmaşık bilgilerle zaman kaybettirmeden, sade, uygulanabilir ve yüksek değerli içerikler sunarak; bireylerin öz disiplin kazanmasını, zihinsel farkındalığını artırmasını, hedeflerine ulaşmasını ve sürdürülebilir bir gelişim süreci içinde eyleme geçmesini sağlamak.

Burada:
✅ Haftada 1 Konuklu/Konuksuz Canlı yayınlar
✅ Haftada 1 Soru/Cevap Etkinlikleri
✅ Konu başlıklarıyla sistematik ilerlemeler
✅ E-Kitaplar ve Pdfler
✅ Sıralama ve Rozet sistemleri
✅ Ayın konusuna göre kitap özetleri
✅ Uygulanabilir sistemler  
✅ Özel PDF''ler ve rehberler  
✅ Sadece üyelerin erişebileceği içerikler

Ama en önemlisi:  
✨ Burada yalnız değilsin  
✨ Burada gelişim bilinçli  
✨ Burada kendine liderlik etmen için her şey hazır

Şimdi birkaç soru soracağım.  
Çünkü herkesin yolu farklı… Senin yönünü birlikte bulalım. 🧭', 2, 1.0, true),

('payment', 'Teşekkür', 'Teşekkür ederim. Cevapların ulaştı ✅

Kompass Network tam da senin gibi düşünen, hisseden ve gelişmek isteyen insanlarla dolu.  
Ve artık hazırsın...', 1, 1.0, true),

('payment', 'Üyelik Başlat', 'Şimdi sana özel üyeliğini başlatmak için sadece bir adım kaldı.

Aşağıdaki linkten Kompass Network''e katılabilirsin.  
📎 [Ödeme linki ve dekont yükleme mesajı]

Şimdi katıl → ve kendine liderlik etmeye başla.', 2, 1.0, true)

ON CONFLICT (type, order_index) DO NOTHING;
