# QuantDB Authentication & Role-Based Access Control (RBAC) Architecture

## 1. Overview & Objectives

QuantDB implements a secure, database-backed authentication and Role-Based Access Control (RBAC) system. The authentication system connects directly to the MySQL database (hosted on Aiven in REAL mode or fallback simulation in MOCK mode) and enforces granular module-level permissions across four platform roles.

Key Architectural Guarantees:
- **No Hardcoded Credentials**: All authentication queries are resolved against the MySQL `users` table using parameterized queries (`%s`).
- **Cryptographic Password Security**: Passwords are never stored in plaintext; they are hashed using **PBKDF2-HMAC-SHA256** with 600,000 iterations (OWASP recommended standard) and cryptographically random salts.
- **Constant-Time Hash Verification**: Employs `hmac.compare_digest` to eliminate side-channel timing attack vectors.
- **Server-Side Guard Enforcement**: Direct URL navigation to unauthorized pages is intercepted at the controller level with automated session guards (`require_auth()`).
- **Zero Credential Leaks**: Password hashes are strictly omitted from UI dataframes, API responses, and session payloads.

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
1. **`USER`**: Standard viewer account. Can monitor markets, inspect portfolio health, and review generated analytical reports. Cannot place orders, configure backtests, or manage strategies.
2. **`QUANT_TRADER`**: Execution-focused role. Permitted to place virtual/paper simulated orders (Market and Limit tickets), manage simulated positions, view strategies, and track execution logs. Real-money trading is strictly disallowed.
3. **`QUANT_RESEARCHER`**: Quantitative modeling role. Permitted to inspect high-resolution historical time-series, run parametric backtests, configure quantitative strategies, compare Sharpe/Drawdown distributions, and generate risk reports. Trading operations are restricted.
4. **`ADMIN`**: Platform governance role. Full access across all application modules, system topology health inspection, database connection diagnostics, and user management (role promotion, account status changes, and secure password resets).

---

## 3. Authentication & Authorization Flow

```text
User Enters Credentials (Username/Email + Password)
                        ↓
            dashboard.services.auth_service.login()
                        ↓
             src.auth.service.authenticate_user()
                        ↓
           Query MySQL `users` via Repository (Parameterized)
                        ↓
           PBKDF2-HMAC-SHA256 Hash Verification (hmac.compare_digest)
                        ↓
           Account Status Verification (Status must be 'ACTIVE')
                        ↓
           Role Normalization (e.g., SIMULATED_TRADER → QUANT_TRADER)
                        ↓
         Populate Streamlit Session State (Omits password & hashes)
                        ↓
       RBAC Navigation & Controller Guards (require_auth)
                        ↓
        Protected Terminal Pages Render with Dynamic Menu
```

---

## 4. Database Schema & Migration

### Schema Modification
The foundational table `users` in `database/02_create_tables.sql` and the migration script `database/12_authentication.sql` define the following structure:

```sql
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT AUTO_INCREMENT,
    username VARCHAR(50) NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM(
        'USER',
        'QUANT_TRADER',
        'QUANT_RESEARCHER',
        'ADMIN',
        'SIMULATED_TRADER'
    ) NOT NULL,
    status ENUM(
        'ACTIVE',
        'INACTIVE',
        'SUSPENDED'
    ) NOT NULL,
    created_at DATETIME NOT NULL,

    PRIMARY KEY (user_id),
    UNIQUE (email),
    UNIQUE (username)
);
```

### Migration (`database/12_authentication.sql`)
The migration is fully idempotent and performs:
1. Expansion of `role` ENUM column to support canonical RBAC roles.
2. Dynamic column addition for `username` (if not exists).
3. Migration of legacy accounts: setting `username` from email prefix and mapping legacy `SIMULATED_TRADER` roles to `QUANT_TRADER`.
4. Creation of UNIQUE index `uq_users_username`.
5. Upgrade of legacy seed hashes to PBKDF2-HMAC-SHA256.
6. Insertion of canonical demonstration accounts.

---

## 5. Password Security Specifications

- **Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 600,000 (compliant with current OWASP security recommendations)
- **Salt**: 16 bytes cryptographically secure random bytes generated via `os.urandom(16)`
- **Format**: `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`
- **Verification**: Evaluated using `hmac.compare_digest(candidate, expected)` to prevent timing side-channel exploits.

---

## 6. Environment & Streamlit Secrets Configuration

### Local Environment (`.env`)
```bash
# Database Configuration
DB_HOST=your-aiven-mysql-host.aivencloud.com
DB_PORT=3306
DB_NAME=QuantDB
DB_USER=avnadmin
DB_PASSWORD=your_secure_password

# Operating Mode ('real' for MySQL Aiven, 'mock' for local time-series simulation)
DATA_MODE=real
```

### Streamlit Community Cloud Secrets (`.streamlit/secrets.toml`)
```toml
DB_HOST = "your-aiven-mysql-host.aivencloud.com"
DB_PORT = "3306"
DB_NAME = "QuantDB"
DB_USER = "avnadmin"
DB_PASSWORD = "your_secure_password"
DATA_MODE = "real"
```

---

## 7. Demonstration Accounts for Academic Evaluation

For testing and academic evaluation, four pre-configured accounts are provided:

| Role | Username | Demonstration Password | Primary Capabilities |
|---|---|---|---|
| **Admin** | `admin01` | `Admin01@QuantDB` | Full system governance, user administration, all modules |
| **Quant Researcher** | `researcher01` | `Researcher01@QuantDB` | Strategy backtesting, analytics, portfolio, market data |
| **Quant Trader** | `trader01` | `Trader01@QuantDB` | Simulated paper order execution, orders table, quotes |
| **Standard User** | `user01` | `User01@QuantDB` | Overview metrics, market data inspection, reports |

> **Note**: In compliance with academic evaluation standards, demo accounts are documented here for demonstration and testing purposes. In production environments, passwords must be rotated immediately using the Admin Console.

---

## 8. User Management via Admin Console

Administrators can manage users directly in the **Admin Console** (`pages/admin.py`):
1. **User Accounts Table**: Displays active accounts, roles, and status without exposing sensitive password hashes.
2. **Update Role & Account Status**: Promotes/demotes user roles (`USER`, `QUANT_TRADER`, `QUANT_RESEARCHER`, `ADMIN`) and toggles account states (`ACTIVE`, `INACTIVE`, `SUSPENDED`).
3. **Secure Password Reset**: Re-hashes and updates passwords using PBKDF2 without exposing plaintext values.
4. **Register New User**: Provisions new accounts directly into the MySQL database with verified password hashing.
