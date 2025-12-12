# Dynamic Configuration Reference

**Status**: ✅ COMPLETE  
**Date**: December 12, 2025

All security features (audit logs, session timeout, 2FA) are now **fully dynamic** and configurable via environment variables.

---

## Backend Configuration (Server)

### Audit Logging

```env
# Enable/disable audit logging
AUDIT_LOG_ENABLED=true

# Log file location
AUDIT_LOG_FILE=audit.log

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
AUDIT_LOG_LEVEL=INFO
```

**Usage in Python:**
```python
from app.core.config import settings

if settings.AUDIT_LOG_ENABLED:
    log_audit(...)

# Log file is written to: settings.AUDIT_LOG_FILE
```

---

### Session Management

```env
# Session timeout in minutes (default: 15)
SESSION_TIMEOUT_MINUTES=15

# Warning time before logout in seconds (default: 60)
SESSION_WARNING_SECONDS=60

# Debounce time for activity tracking in milliseconds (default: 5000)
ACTIVITY_DEBOUNCE_MS=5000
```

**Usage in Python:**
```python
from app.core.config import settings

# Get timeout from config
timeout_min = settings.SESSION_TIMEOUT_MINUTES
warning_sec = settings.SESSION_WARNING_SECONDS
```

**Examples:**

```env
# Development: 30 minute timeout, 90 second warning
SESSION_TIMEOUT_MINUTES=30
SESSION_WARNING_SECONDS=90

# Production: 15 minute timeout, 60 second warning
SESSION_TIMEOUT_MINUTES=15
SESSION_WARNING_SECONDS=60

# Sensitive operations: 5 minute timeout, 30 second warning
SESSION_TIMEOUT_MINUTES=5
SESSION_WARNING_SECONDS=30
```

---

### Two-Factor Authentication (2FA)

```env
# Enable/disable 2FA globally
TWO_FACTOR_ENABLED=true

# Number of backup codes generated during setup (default: 10)
TWO_FACTOR_BACKUP_CODES=10

# TOTP time window tolerance in 30-second intervals (default: 1)
# Valid_window=1 means ±30 seconds (current + previous + next)
TWO_FACTOR_TOTP_WINDOW=1

# Comma-separated list of roles that require 2FA
TWO_FACTOR_REQUIRED_ROLES=admin,manager

# Rate limit for 2FA verification attempts
TWO_FACTOR_RATE_LIMIT=5/minute
```

**Usage in Python:**
```python
from app.core.config import settings

# Check if 2FA is required for user role
if user.role in settings.TWO_FACTOR_REQUIRED_ROLES:
    require_2fa(user)

# Generate backup codes using configured count
codes = TwoFactorAuthService.get_backup_codes()  # Uses TWO_FACTOR_BACKUP_CODES
```

**Examples:**

```env
# Require 2FA for all roles
TWO_FACTOR_REQUIRED_ROLES=admin,manager,cashier,clerk

# Require 2FA only for admin
TWO_FACTOR_REQUIRED_ROLES=admin

# Generate 15 backup codes instead of 10
TWO_FACTOR_BACKUP_CODES=15

# More lenient TOTP window (±60 seconds)
TWO_FACTOR_TOTP_WINDOW=2
```

---

## Frontend Configuration (Client)

### Session Management

```env
# Session timeout in minutes (MUST match backend)
NEXT_PUBLIC_SESSION_TIMEOUT_MIN=15

# Warning time before logout in seconds (MUST match backend)
NEXT_PUBLIC_SESSION_WARNING_SEC=60

# Debounce time for activity tracking in milliseconds
NEXT_PUBLIC_ACTIVITY_DEBOUNCE_MS=5000
```

**Usage in TypeScript:**
```typescript
import { useSessionTimeout } from '@/lib/useSessionTimeout';

// Hook automatically uses environment variables
const { showWarning, timeRemaining } = useSessionTimeout();

// Or override with props
const custom = useSessionTimeout({
  timeoutMinutes: 20,  // Override env variable
});
```

### Two-Factor Authentication

```env
# Enable/disable 2FA in frontend
NEXT_PUBLIC_TWO_FACTOR_ENABLED=true
```

**Usage in TypeScript:**
```typescript
if (process.env.NEXT_PUBLIC_TWO_FACTOR_ENABLED === 'true') {
  return <TwoFactorSetup />;
}
```

### API Configuration

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Publishable Key (frontend safe)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
```

---

## Configuration Examples

### Development Environment

```env
# .env.development

# Relaxed timeouts for development
SESSION_TIMEOUT_MINUTES=60
SESSION_WARNING_SECONDS=30

# More backup codes for testing
TWO_FACTOR_BACKUP_CODES=20

# Verbose audit logging
AUDIT_LOG_LEVEL=DEBUG

# Frontend
NEXT_PUBLIC_SESSION_TIMEOUT_MIN=60
NEXT_PUBLIC_SESSION_WARNING_SEC=30
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Environment

```env
# .env.production

# Strict security settings
SESSION_TIMEOUT_MINUTES=15
SESSION_WARNING_SECONDS=60
ACTIVITY_DEBOUNCE_MS=3000

# 2FA required for sensitive roles
TWO_FACTOR_ENABLED=true
TWO_FACTOR_REQUIRED_ROLES=admin,manager

# Conservative backup codes
TWO_FACTOR_BACKUP_CODES=10

# Restrictive audit logging
AUDIT_LOG_LEVEL=WARNING
AUDIT_LOG_FILE=/var/log/vendly/audit.log

# Frontend
NEXT_PUBLIC_SESSION_TIMEOUT_MIN=15
NEXT_PUBLIC_SESSION_WARNING_SEC=60
NEXT_PUBLIC_API_URL=https://api.vendly.com
```

### High-Security / PCI Environment

```env
# .env.pci-compliance

# Very short timeout for sensitive operations
SESSION_TIMEOUT_MINUTES=5
SESSION_WARNING_SECONDS=30
ACTIVITY_DEBOUNCE_MS=2000

# 2FA for ALL roles
TWO_FACTOR_ENABLED=true
TWO_FACTOR_REQUIRED_ROLES=admin,manager,cashier,clerk

# Strict TOTP window (no tolerance)
TWO_FACTOR_TOTP_WINDOW=0

# Generate more backup codes
TWO_FACTOR_BACKUP_CODES=20

# Comprehensive audit logging
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=DEBUG
AUDIT_LOG_FILE=/var/log/vendly/audit.log

# Frontend
NEXT_PUBLIC_SESSION_TIMEOUT_MIN=5
NEXT_PUBLIC_SESSION_WARNING_SEC=30
```

---

## Loading Environment Variables

### Backend (Python)

```python
from app.core.config import settings

# Automatically loads from .env file
print(settings.SESSION_TIMEOUT_MINUTES)  # 15
print(settings.TWO_FACTOR_BACKUP_CODES)  # 10
print(settings.AUDIT_LOG_FILE)  # audit.log
```

### Frontend (Next.js)

```typescript
// Automatically loaded from .env.local or .env
const timeout = process.env.NEXT_PUBLIC_SESSION_TIMEOUT_MIN;  // "15"
const warningTime = parseInt(process.env.NEXT_PUBLIC_SESSION_WARNING_SEC || "60");

// Used in hooks
const { showWarning } = useSessionTimeout({
  timeoutMinutes: parseInt(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_MIN || "15"),
});
```

---

## Configuration Files Hierarchy

### Backend (.env files)

1. `.env` - Local/current environment (not in git)
2. `.env.example` - Template with default values (in git)
3. `docker-compose.yml` - Docker environment variables
4. `server/app/core/config.py` - Python defaults

### Frontend (.env files)

1. `.env.local` - Local only (not in git)
2. `.env` - All environments (not in git)
3. `.env.development` - Development specific
4. `.env.production` - Production specific
5. `.env.example` - Template (in git)

---

## .env File Setup

### 1. Create .env from template

```bash
cd /path/to/Vendly-fastapi-Js

# Backend
cp .env.example server/.env

# Frontend
cp client/.env.example client/.env.local
```

### 2. Update values for your environment

**Backend** (`server/.env`):
```env
# Development
SESSION_TIMEOUT_MINUTES=30
AUDIT_LOG_ENABLED=true

# Production
# SESSION_TIMEOUT_MINUTES=15
# AUDIT_LOG_ENABLED=true
```

**Frontend** (`client/.env.local`):
```env
NEXT_PUBLIC_SESSION_TIMEOUT_MIN=30
NEXT_PUBLIC_SESSION_WARNING_SEC=60
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Load configuration

```bash
# Backend: configuration is auto-loaded
python -m uvicorn app.main:app --reload

# Frontend: Next.js auto-loads environment variables
npm run dev
```

---

## Verification

### Check Backend Configuration

```python
# In Python shell or test file
from app.core.config import settings

print("Session Timeout:", settings.SESSION_TIMEOUT_MINUTES, "minutes")
print("Session Warning:", settings.SESSION_WARNING_SECONDS, "seconds")
print("2FA Enabled:", settings.TWO_FACTOR_ENABLED)
print("2FA Backup Codes:", settings.TWO_FACTOR_BACKUP_CODES)
print("Audit Log File:", settings.AUDIT_LOG_FILE)
print("Audit Logging:", "Enabled" if settings.AUDIT_LOG_ENABLED else "Disabled")
```

### Check Frontend Configuration

```typescript
// In browser console or test file
console.log("Session Timeout (min):", process.env.NEXT_PUBLIC_SESSION_TIMEOUT_MIN);
console.log("Session Warning (sec):", process.env.NEXT_PUBLIC_SESSION_WARNING_SEC);
console.log("API URL:", process.env.NEXT_PUBLIC_API_URL);
console.log("2FA Enabled:", process.env.NEXT_PUBLIC_TWO_FACTOR_ENABLED);
```

---

## Dynamic Configuration at Runtime

### Change Session Timeout Programmatically

```python
# Backend - Modify environment variable
import os
os.environ['SESSION_TIMEOUT_MINUTES'] = '10'

# Reload settings
from importlib import reload
import app.core.config as config_module
reload(config_module)
from app.core.config import settings
print(settings.SESSION_TIMEOUT_MINUTES)  # 10
```

### Per-User Session Timeout (Advanced)

```python
# Backend - Store user-specific timeout in database
class UserSettings(Base):
    user_id: int
    session_timeout_minutes: Optional[int]  # None = use global default

# When checking session
def get_user_timeout(user_id: int, db: Session):
    user_settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    if user_settings and user_settings.session_timeout_minutes:
        return user_settings.session_timeout_minutes
    return settings.SESSION_TIMEOUT_MINUTES
```

---

## Troubleshooting Configuration

### Frontend not reading environment variables

1. **Restart dev server** after changing `.env.local`
   ```bash
   npm run dev
   ```

2. **Verify file location** - Must be in project root, not in `client/`
   ```bash
   # Correct
   .env.local
   
   # Wrong (Next.js won't find it)
   client/.env.local
   ```

3. **Use NEXT_PUBLIC_ prefix** for browser-accessible variables
   ```env
   # ✅ Frontend can see this
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # ❌ Frontend cannot see this
   PRIVATE_API_KEY=secret
   ```

### Backend not reading environment variables

1. **Check file location** - Must be in backend directory or project root
   ```bash
   # Backend looks for .env in current working directory
   # When running from server/ directory
   cd server
   python -m uvicorn app.main:app  # Looks in server/.env
   ```

2. **Verify variable name** - Must match config.py Field names
   ```python
   # In config.py
   SESSION_TIMEOUT_MINUTES: int = Field(default=15, alias="SESSION_TIMEOUT_MINUTES")
   
   # In .env (must use exact name)
   SESSION_TIMEOUT_MINUTES=15
   ```

3. **Restart backend** after changing `.env`
   ```bash
   # Kill and restart
   python -m uvicorn app.main:app --reload
   ```

---

## Best Practices

1. **Never commit .env files** to git
   - Add to `.gitignore`
   - Keep `.env.example` as template

2. **Match frontend and backend timeouts**
   ```env
   # Backend
   SESSION_TIMEOUT_MINUTES=15
   
   # Frontend - MUST MATCH
   NEXT_PUBLIC_SESSION_TIMEOUT_MIN=15
   ```

3. **Use environment-specific config files**
   ```bash
   .env.development  # Local development
   .env.production   # Production settings
   .env.pci          # PCI compliance
   ```

4. **Document all configuration options**
   - Use `.env.example` as living documentation
   - Add comments explaining each setting

5. **Validate configuration on startup**
   ```python
   # In app startup
   assert settings.SESSION_TIMEOUT_MINUTES > 0
   assert settings.SESSION_WARNING_SECONDS < settings.SESSION_TIMEOUT_MINUTES * 60
   ```

---

## Summary

**All features are now fully dynamic:**

✅ Session timeout - Environment variable  
✅ Session warning - Environment variable  
✅ Activity debounce - Environment variable  
✅ 2FA enabled/disabled - Environment variable  
✅ 2FA backup codes - Environment variable  
✅ 2FA TOTP window - Environment variable  
✅ 2FA required roles - Environment variable  
✅ Audit logging enabled - Environment variable  
✅ Audit log file - Environment variable  
✅ Audit log level - Environment variable  

**No hardcoded values!** Everything is configurable.
