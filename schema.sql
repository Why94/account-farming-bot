-- ============================================
--  Schema untuk tabel stok_akun
--  Jalankan di PostgreSQL:
--    psql -U <user> -d <dbname> -f schema.sql
-- ============================================

CREATE TABLE IF NOT EXISTS stok_akun (
    id          SERIAL PRIMARY KEY,
    kategori    VARCHAR(50)  NOT NULL,
    data_akun   TEXT         NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'ready',
    session_data TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Index untuk query cepat berdasarkan kategori & status
CREATE INDEX IF NOT EXISTS idx_stok_akun_kategori
    ON stok_akun (kategori);

CREATE INDEX IF NOT EXISTS idx_stok_akun_status
    ON stok_akun (status);

-- Trigger untuk auto-update updated_at
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON stok_akun;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON stok_akun
    FOR EACH ROW
    EXECUTE FUNCTION trg_set_updated_at();

-- Contoh insert manual (untuk testing):
-- INSERT INTO stok_akun (kategori, data_akun, status)
-- VALUES ('runway', 'test@mail.com|Test123!', 'ready');
