CREATE TABLE IF NOT EXISTS pending_registrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(180) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    verification_code_hash VARCHAR(64) NOT NULL,
    verification_expires_at TIMESTAMP NOT NULL,
    verification_sent_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_pending_registrations_email ON pending_registrations(email);
CREATE INDEX IF NOT EXISTS ix_pending_registrations_phone ON pending_registrations(phone);
