ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_hash VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_expires_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_sent_at TIMESTAMP NULL;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS product_type VARCHAR(20) NOT NULL DEFAULT 'vehicle';
UPDATE listings SET product_type='vehicle' WHERE product_type IS NULL OR product_type='';
