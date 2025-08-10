-- SSS tipini messages tablosuna ekleme
-- Bu SQL'i Supabase SQL Editor'da çalıştırın

-- Önce mevcut CHECK constraint'i kaldır
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_type_check;

-- Yeni CHECK constraint ekle (sss tipini dahil ederek)
ALTER TABLE messages ADD CONSTRAINT messages_type_check 
    CHECK (type IN ('welcome', 'question', 'payment', 'sss'));

-- Varsayılan SSS mesajını ekle
INSERT INTO messages (type, title, content, order_index, delay, is_active) VALUES
('sss', 'Sık Sorulan Sorular', '❓ **Sık Sorulan Sorular (SSS)**

Ödeme yaptıktan sonra ne olacak?
Bot, ödemenizi onaylar ve sizi otomatik olarak özel Telegram grubuna ekler.

Program süreci nasıl olacak?
Örneğin:
	•	İlk 7 gün: Farkındalık
	•	Sonraki 1 ay: Amaç bulma
	•	Sonraki ay: Hedefler ve planlara ayırma
	•	Sonraki ay: Disiplin inşası
Ve her ay yeni bir konu eklenecek.

Üyeliğimi istediğim zaman iptal edebilir miyim?
Evet, üyeliğinizi istediğiniz zaman admin ile iletişime geçerek iptal edebilirsiniz(Gruptan çıkışınız sağlanacaktır).


Daha önce kişisel gelişimle ilgilenmedim, katılabilir miyim?
Evet. Kompass Network, sıfırdan başlayanlar için bile planlı ve adım adım ilerleyen bir sistem sunar.

Katıldığımda geriye dönük içeriklere ulaşabilecek miyim?
Evet, katıldığınız andan itibaren arşive erişiminiz olur.

Üyelik ücreti dışında başka bir ücret ödeyecek miyim?
Hayır, tüm içerikler ve topluluk erişimi üyelik ücretine dahildir.

Ödemelerim güvenli mi?
Evet, tüm ödemeler Shopier güvencesiyle 256 bit SSL sertifikasıyla yapılır.

Başka sorularınız var mı?
Ek sorularınız için admin ile iletişime geçebilirsiniz.

)
ON CONFLICT (type, order_index) DO NOTHING;

-- Değişiklikleri doğrula
SELECT type, COUNT(*) as count FROM messages GROUP BY type ORDER BY type;
