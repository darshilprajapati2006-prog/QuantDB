USE QuantDB;

-- Keep this role list aligned with src/auth/roles.py.
ALTER TABLE users
    MODIFY COLUMN role ENUM(
        'USER',
        'QUANT_TRADER',
        'QUANT_RESEARCHER',
        'QUANT_DEVELOPER',
        'ADMIN',
        'SIMULATED_TRADER'
    ) NOT NULL;

CREATE TABLE IF NOT EXISTS role_change_requests (
    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    requested_role VARCHAR(40) NOT NULL,
    reason VARCHAR(500) NOT NULL DEFAULT '',
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,
    reviewed_by BIGINT NULL,
    INDEX idx_role_requests_user_status (user_id, status),
    INDEX idx_role_requests_status_created (status, created_at)
);
