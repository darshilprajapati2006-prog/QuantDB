-- File: 13_signup_otp_verification.sql
-- QuantDB User Registration & Email OTP Verification Migration
-- Safe, repeatable migration script for MySQL 8.x.

USE QuantDB;

-- 1. Add is_verified column to users table if not already present
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'users' 
      AND COLUMN_NAME = 'is_verified'
);

SET @sql_add_col = IF(
    @col_exists = 0,
    'ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE AFTER status',
    'DO 0'
);

PREPARE stmt FROM @sql_add_col;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. Mark all existing platform accounts as verified
UPDATE users 
SET is_verified = TRUE 
WHERE is_verified = FALSE;

-- 3. Create email_otps verification table
CREATE TABLE IF NOT EXISTS email_otps (
    otp_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    otp_hash VARCHAR(255) NOT NULL,
    purpose VARCHAR(30) NOT NULL DEFAULT 'REGISTRATION',
    expires_at DATETIME NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    verified_at DATETIME NULL,

    PRIMARY KEY (otp_id),
    CONSTRAINT fk_email_otps_user FOREIGN KEY (user_id) 
        REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_email_otps_user_purpose (user_id, purpose, is_used),
    INDEX idx_email_otps_expires (expires_at)
);
