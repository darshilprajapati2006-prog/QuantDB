USE QuantDB;

CREATE TABLE IF NOT EXISTS account_invitations (
    invitation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT '',
    role ENUM('USER', 'QUANT_TRADER', 'QUANT_RESEARCHER', 'QUANT_DEVELOPER') NOT NULL DEFAULT 'USER',
    status ENUM('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED') NOT NULL DEFAULT 'PENDING',
    created_by BIGINT NOT NULL,
    accepted_user_id BIGINT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    accepted_at DATETIME NULL,
    active_email VARCHAR(150) GENERATED ALWAYS AS (CASE WHEN status = 'PENDING' THEN LOWER(email) ELSE NULL END) STORED,
    UNIQUE KEY uq_account_invitation_pending_email (active_email),
    INDEX idx_invitations_email_status (email, status),
    INDEX idx_invitations_status_expiry (status, expires_at)
);

UPDATE account_invitations
SET status = 'EXPIRED'
WHERE status = 'PENDING' AND expires_at <= CURRENT_TIMESTAMP;
