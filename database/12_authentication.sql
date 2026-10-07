-- File: 12_authentication.sql
-- QuantDB Authentication & Role-Based Access Control (RBAC) Migration
-- Safe, repeatable migration script for MySQL 8.x.

USE QuantDB;

-- 1. Extend Role ENUM on users table to support canonical RBAC roles
-- Supports: USER, QUANT_TRADER, QUANT_RESEARCHER, ADMIN (and legacy SIMULATED_TRADER)
ALTER TABLE users 
MODIFY COLUMN role ENUM(
    'USER',
    'QUANT_TRADER',
    'QUANT_RESEARCHER',
    'ADMIN',
    'SIMULATED_TRADER'
) NOT NULL;

-- 2. Add username column if not already present
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'users' 
      AND COLUMN_NAME = 'username'
);

SET @sql_add_col = IF(
    @col_exists = 0,
    'ALTER TABLE users ADD COLUMN username VARCHAR(50) NULL AFTER user_id',
    'DO 0'
);

PREPARE stmt FROM @sql_add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. Populate username for existing accounts based on email prefix
UPDATE users 
SET username = LOWER(SUBSTRING_INDEX(email, '@', 1))
WHERE username IS NULL OR username = '';

-- 4. Migrate legacy SIMULATED_TRADER roles to QUANT_TRADER
UPDATE users 
SET role = 'QUANT_TRADER' 
WHERE role = 'SIMULATED_TRADER';

-- 5. Add unique index on username if not already present
SET @idx_exists = (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'users' 
      AND (INDEX_NAME = 'uq_users_username' OR INDEX_NAME = 'username')
);

SET @sql_add_idx = IF(
    @idx_exists = 0,
    'ALTER TABLE users ADD CONSTRAINT uq_users_username UNIQUE (username)',
    'DO 0'
);

PREPARE stmt_idx FROM @sql_add_idx;
EXECUTE stmt_idx;
DEALLOCATE PREPARE stmt_idx;

-- 6. Update existing legacy users with cryptographically secure PBKDF2 hashes
UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$a39e542b01770e3b44a2ccd246ea934f$aac4a7c1620170c01d3ee1f4f7616d5313d69e89d87a2d7e3c81403265303026'
WHERE email = 'aarav@quantdb.com' AND password_hash LIKE 'hash_%';

UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$c3a0173d963eb0b17a2a7999891ceba5$987a07f09762acc90f38ddb6954734f7bf413fb4d35f8f6e7fdc23e2af8ef253'
WHERE email = 'riya@quantdb.com' AND password_hash LIKE 'hash_%';

UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$bf72e28c75bf1b049f991e0afddbc92c$c1a61ea7255edb59048bb7926af845b3f8779d198985facac713a0ad0c404a78'
WHERE email = 'karan@quantdb.com' AND password_hash LIKE 'hash_%';

UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$886052693d2589c4d6bed334ceeacfa6$3912c5682eb6a760c643b138992f1e790d479b38b15f7dea750ed5c49ce9c513'
WHERE email = 'neha@quantdb.com' AND password_hash LIKE 'hash_%';

UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$712bab81a23ab3fc5964ffe3028fd250$6b5fbd71616ae92a10aadbc4e04f0b3598d3b749936f00a4952c183393e5e494'
WHERE email = 'arjun@quantdb.com' AND password_hash LIKE 'hash_%';

UPDATE users 
SET password_hash = 'pbkdf2_sha256$600000$fb0aec4ac0f9d5c5a381682aa3f739d1$ae5d6fe74c9b0a7d8a2df83d3fa864526fc2e02cae265e6567fdbd09617f1023'
WHERE email = 'priya@quantdb.com' AND password_hash LIKE 'hash_%';

-- 7. Seed canonical demo accounts for the 4 platform roles
-- Stored password hashes are generated using PBKDF2-HMAC-SHA256 (600,000 iterations)
-- Demo credentials:
-- user01       -> User01@QuantDB       (Role: USER)
-- trader01     -> Trader01@QuantDB     (Role: QUANT_TRADER)
-- researcher01 -> Researcher01@QuantDB (Role: QUANT_RESEARCHER)
-- admin01      -> Admin01@QuantDB      (Role: ADMIN)

INSERT INTO users (username, name, email, password_hash, role, status, created_at)
VALUES
    ('user01', 'Standard User', 'user01@quantdb.local',
     'pbkdf2_sha256$600000$d0a9adf2bdf13b0f357b83aff53c3639$681bfc65c577d20edfe62e3dfd08b38b4f5a82e8755e54aa455f47a24563a3f5',
     'USER', 'ACTIVE', '2026-03-01 09:00:00'),

    ('trader01', 'Quant Trader Demo', 'trader01@quantdb.local',
     'pbkdf2_sha256$600000$901db324942678e05085bcdf4fa5716e$870aa7bd982824b3f1a916d27b4b9301a41646da78d276ae4dd897163a36322c',
     'QUANT_TRADER', 'ACTIVE', '2026-03-01 09:15:00'),

    ('researcher01', 'Quant Researcher Demo', 'researcher01@quantdb.local',
     'pbkdf2_sha256$600000$46737cc62c306bcbf7e8bb52c18e2e94$ed59f1ad880f9ea45f90d81aea3949647d3616fa094337a2067087426a4faf12',
     'QUANT_RESEARCHER', 'ACTIVE', '2026-03-01 09:30:00'),

    ('admin01', 'Admin Demo', 'admin01@quantdb.local',
     'pbkdf2_sha256$600000$c18765d7c83c91627542564fcaa5a191$4503e12c8e2a161d8b4b6f8acf06e5821b9037990503caf5f3e02fd79eeab37d',
     'ADMIN', 'ACTIVE', '2026-03-01 09:45:00')
ON DUPLICATE KEY UPDATE 
    password_hash = VALUES(password_hash),
    role = VALUES(role),
    status = VALUES(status);
