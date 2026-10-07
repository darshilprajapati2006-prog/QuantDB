# QuantDB Authentication, Registration & Role-Based Access Control (RBAC) Architecture

## 1. Overview & Objectives

QuantDB implements a secure, database-backed authentication, self-registration with real Email OTP verification, and Role-Based Access Control (RBAC) system. The authentication system connects directly to the MySQL database (hosted on Aiven in REAL mode or fallback simulation in MOCK mode) and enforces granular module-level permissions across four platform roles.

Key Architectural Guarantees:
- **No Hardcoded Credentials**: All authentication and registration queries are resolved against the MySQL `users` and `email_otps` tables using parameterized queries (`%s`).
- **Cryptographic Password Security**: Passwords are never stored in plaintext; they are hashed using **PBKDF2-HMAC-SHA256** with 600,000 iterations (OWASP recommended standard) and cryptographically random salts.
- **Cryptographic OTP Security**: 6-digit verification codes are generated using Python's `secrets` module, salted, and hashed using SHA-256 before persistence in MySQL. Plaintext OTPs are never stored in the database and never logged.
- **Constant-Time Verification**: Employs `hmac.compare_digest` to eliminate side-channel timing attack vectors for both password and OTP comparisons.
- **Enforced Verification Gate**: Accounts start with `is_verified = FALSE`. Unverified accounts cannot authenticate or access any platform modules.
- **Strict Role Boundary on Registration**: Public registration strictly assigns the default `USER` role. Privileged roles (`ADMIN`, `QUANT_TRADER`, `QUANT_RESEARCHER`) cannot be self-selected and must be assigned by Platform Administrators.
- **Server-Side Guard Enforcement**: Direct URL navigation to unauthorized pages is intercepted at the controller level with automated session guards (`require_auth()`).
- **Zero Credential Leaks**: Password hashes and OTP hashes are strictly omitted from UI dataframes, API responses, and session payloads.

---

## 2. Platform Roles & Permission Matrix

The system provides four logical roles with strict separation of concerns:

| Platform Module | USER | QUANT_TRADER | QUANT_RESEARCHER | ADMIN |
|---|:---:|:---:|:---:|:---:|
| **Terminal Overview** | ✓ Allowed | ✓ Allowed | ✓ Allowed | ✓ Allowed |
| **Market Data Research** | ✓ Read Only | ✓ Read Only | ✓ Read Only | ✓ Full Read |
| **Simulated Trading** | ✗ Restricted | ✓ Paper Trading Only | ✗ Restricted | ✓ Full Paper Trading |
| **Portfolio Analytics** | ✓ Allowed | ✓ Allowed | ✓ Allowed | ✓ All Portfolios |
| **Strategy Library** | ✗ Restricted | ✓ View Only | ✓ Full Access | ✓ Full Access |
| **Strategy Backtesting**| ✗ Restricted | ✗ Restricted | ✓ Full Execution | ✓ Full Execution |
| **Analytics & Reports** | ✓ Allowed | ✓ Allowed | ✓ Allowed | ✓ Allowed |
| **Admin Console** | ✗ Restricted | ✗ Restricted | ✗ Restricted | ✓ Full Governance |

### Role Descriptions
1. **`USER`**: Standard viewer account. Default role for all self-registered users. Can monitor markets, inspect portfolio health, and review generated analytical reports. Cannot place orders, configure backtests, or manage strategies.
2. **`QUANT_TRADER`**: Execution-focused role. Permitted to place virtual/paper simulated orders (Market and Limit tickets), manage simulated positions, view strategies, and track execution logs. Real-money trading is strictly disallowed.
3. **`QUANT_RESEARCHER`**: Quantitative modeling role. Permitted to inspect high-resolution historical time-series, run parametric backtests, configure quantitative strategies, compare Sharpe/Drawdown distributions, and generate risk reports. Trading operations are restricted.
4. **`ADMIN`**: Platform governance role. Full access across all application modules, system topology health inspection, database connection diagnostics, and user management (role promotion, account status changes, and secure password resets).

---

## 3. User Registration & Email OTP Verification Flow

```text
User Submits Sign Up Form (Full Name, Username, Email, Password, Confirm Password)
                                    ↓
            dashboard.services.auth_service.signup()
                                    ↓
             src.auth.service.register_user()
                                    ↓
    Server-side Validation (Formats, Min Strength, Match, Uniqueness)
                                    ↓
      Role Enforcement: Strictly Force Role = Role.USER
                                    ↓
     Hash Password (PBKDF2-HMAC-SHA256) & Store Pending User (is_verified = FALSE)
                                    ↓
  Generate 6-Digit Cryptographic OTP (secrets) & Salted Hash (SHA-256)
                                    ↓
         Store OTP Hash in MySQL `email_otps` (5-minute expiry)
                                    ↓
            Dispatch OTP via SMTP Email (TLS / SSL)
                                    ↓
        User Enters 6-Digit Code on Verification Screen
                                    ↓
         src.auth.service.verify_registration_otp()
                                    ↓
      Validate Expiry (< 5 min) & Attempt Counter (<= 5 attempts)
                                    ↓
         Verify OTP Hash (hmac.compare_digest)
                                    ↓
       Success: Mark OTP Used & Update User `is_verified = TRUE`
                                    ↓
   Show "Account Verified Successfully" → Continue to Sign In
```

---

## 4. OTP Security & Lifecycle Management

1. **Generation**: Generated via `secrets.randbelow(1000000)` zero-padded to 6 digits (`000000`-`999999`).
2. **Database Persistence**: The plaintext code is hashed with a cryptographically secure 16-byte salt (`sha256$<salt_hex>$<hash_hex>`). Plaintext is discarded immediately after email dispatch.
3. **Expiry Window**: Verification codes expire after **5 minutes** (300 seconds). Expired codes are rejected with an explicit prompt to request a new code.
4. **Attempt Rate-Limiting**: Maximum **5 failed attempts**. If the threshold is exceeded, the OTP is invalidated, blocking brute-force enumeration.
5. **Resend Cooldown**: Enforces a strict server-side **60-second cooldown** between resend requests to prevent mail server flooding.
6. **One-Time Use & Invalidation**: Once verified, `is_used` is set to `TRUE` and `verified_at` timestamp is recorded. Any subsequent submission of the same code is rejected.

---

## 5. Database Schema & Migrations

### Migration `12_authentication.sql`
Expands the `role` enum, adds unique `username` column, and migrates legacy seed accounts.

### Migration `13_signup_otp_verification.sql`
Adds the verification status flag to `users` and creates the dedicated OTP tracking entity `email_otps`:

```sql
-- 1. Add verification column to users table
ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Dedicated OTP verification table
CREATE TABLE IF NOT EXISTS email_otps (
    otp_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    otp_hash VARCHAR(255) NOT NULL,
    purpose VARCHAR(50) NOT NULL DEFAULT 'REGISTRATION',
    expires_at DATETIME NOT NULL,
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    verified_at DATETIME NULL,

    PRIMARY KEY (otp_id),
    CONSTRAINT fk_email_otps_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE,
    INDEX idx_user_purpose (user_id, purpose),
    INDEX idx_expires (expires_at)
);
```

---

## 6. SMTP & Environment Configuration

### Local Environment (`.env`)
```bash
# Database Configuration
DB_HOST=your-aiven-mysql-host.aivencloud.com
DB_PORT=3306
DB_NAME=QuantDB
DB_USER=avnadmin
DB_PASSWORD=your_secure_password
DATA_MODE=real

# SMTP Email Configuration (Required for Real OTP Delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_institutional_account@gmail.com
SMTP_PASSWORD=your_google_app_password
SMTP_FROM_EMAIL=your_institutional_account@gmail.com
SMTP_USE_TLS=true
```

### Streamlit Community Cloud Secrets (`.streamlit/secrets.toml`)
For deployment to Streamlit Community Cloud, configure the secrets directly in the Streamlit Cloud dashboard:
```toml
DB_HOST = "your-aiven-mysql-host.aivencloud.com"
DB_PORT = "3306"
DB_NAME = "QuantDB"
DB_USER = "avnadmin"
DB_PASSWORD = "your_secure_password"
DATA_MODE = "real"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_institutional_account@gmail.com"
SMTP_PASSWORD = "your_google_app_password"
SMTP_FROM_EMAIL = "your_institutional_account@gmail.com"
SMTP_USE_TLS = true
```

> **Gmail App Password Note**: For Gmail, use an **App Password** rather than your Google account password. Navigate to `Google Account → Security → 2-Step Verification → App passwords` and generate an app password for `QuantDB`.

---

## 7. Demonstration Accounts for Academic Evaluation

| Role | Username | Demonstration Password | Primary Capabilities |
|---|---|---|---|
| **Admin** | `admin01` | `Admin01@QuantDB` | Full system governance, user administration, all modules |
| **Quant Researcher** | `researcher01` | `Researcher01@QuantDB` | Strategy backtesting, analytics, portfolio, market data |
| **Quant Trader** | `trader01` | `Trader01@QuantDB` | Simulated paper order execution, orders table, quotes |
| **Standard User** | `user01` | `User01@QuantDB` | Overview metrics, market data inspection, reports |
