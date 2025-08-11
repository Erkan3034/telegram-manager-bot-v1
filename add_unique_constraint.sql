-- Bu SQL'i Supabase SQL Editor'da çalıştırın
-- Grup üyelerinde duplicate kayıtları önlemek için unique constraint ekler

-- Önce mevcut duplicate kayıtları temizle (her kullanıcı için sadece en son kaydı tut)
DELETE FROM group_members 
WHERE id NOT IN (
    SELECT MAX(id) 
    FROM group_members 
    GROUP BY user_id, group_id
);

-- Unique constraint ekle (bir kullanıcı aynı grupta sadece bir kez bulunabilir)
ALTER TABLE group_members 
ADD CONSTRAINT unique_user_group UNIQUE (user_id, group_id);

-- Index ekle (performans için)
CREATE INDEX IF NOT EXISTS idx_group_members_user_group ON group_members(user_id, group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group_status ON group_members(group_id, status);
