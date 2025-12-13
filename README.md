
# Vendly - Enterprise Point of Sale System

A modern, enterprise-grade point-of-sale system built with Next.js 14 (React/TypeScript) frontend and FastAPI (Python) backend. Includes trending AI features, real-time event processing, and robust security.

## 📚 Documentation

**For comprehensive documentation, see the [`docs/`](./docs/) folder:**
- **[Complete Documentation Index](./docs/README.md)** - Start here for all guides
- **[Offline Mode Guide](./docs/OFFLINE_MODE.md)** - Offline sales queueing & sync
- **[Granular Permissions Guide](./docs/GRANULAR_PERMISSIONS.md)** - Role-based access control
- **[Production Deployment Guide](./PRODUCTION_DEPLOYMENT.md)** - Redis, Email & SMS setup for production

## 🏗️ Architecture

Vendly follows a microservices-inspired architecture with event-driven patterns:

```
┌──────────────────────────────────────────────────────────────────┐
│                         VENDLY POS                                │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │ Frontend│────│  Nginx  │────│ Backend │────│  AI/ML  │       │
│  │ (React) │    │ (Proxy) │    │(FastAPI)│    │ Service │       │
│  └─────────┘    └─────────┘    └────┬────┘    └─────────┘       │
│                                     │                            │
│        ┌────────────────────────────┼────────────────────┐       │
│        │                            │                    │       │
│  ┌─────▼─────┐    ┌─────────┐    ┌──▼──────┐    ┌───────▼───┐  │
│  │PostgreSQL │    │  Redis  │    │  Kafka  │    │Prometheus │  │
│  │(Database) │    │ (Cache) │    │(Events) │    │(Metrics)  │  │
│  └───────────┘    └─────────┘    └─────────┘    └───────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
vendly/

├── client/              # Next.js 14 frontend (React, TypeScript, Tailwind)
├── server/              # FastAPI backend (Python 3.11, SQLAlchemy, Alembic)
├── shared/              # Shared types and utilities
├── ai_ml/               # AI/ML services (forecasting, anomaly, recommendations, pricing, LLM, voice)
├── scripts/             # Utility scripts (e.g., seed_products.py for demo data)
├── docker-compose.yaml  # Container orchestration
├── config.example.yaml  # User configuration template
└── .env.example         # Environment template
 

## ✨ New Features (2025)

Vendly now supports advanced refund and return flows, two-factor authentication, plus other improvements:

### Refunds & Returns
- Partial and full refunds for sales, with inventory adjustment.
- Returns flow for items, with employee authorization and reason logging.
- Refund/Return endpoints: `/api/v1/sales/{sale_id}/refund` and `/api/v1/sales/{sale_id}/return`.
- Frontend UI for refund/return in POS, with sale lookup by ID, phone, or name.
- Refund/Return statistics in reports (total refunds, returns, amounts).

### Two-Factor Authentication (2FA) ✅
- **TOTP-based 2FA** (Time-based One-Time Password via Google Authenticator, Microsoft Authenticator, Authy, etc.)
- **Backup codes** (10 codes generated per user for account recovery)
- **Audit logging** of all 2FA events (enable, disable, verification)
- **API endpoints:**
  - `POST /api/v1/auth/2fa/setup` - Initialize 2FA setup
  - `POST /api/v1/auth/2fa/verify` - Verify and enable 2FA
  - `POST /api/v1/auth/2fa/verify-login` - Verify 2FA during login
  - `POST /api/v1/auth/2fa/disable` - Disable 2FA
  - `GET /api/v1/auth/2fa/status` - Check 2FA status
  - `POST /api/v1/auth/2fa/regenerate-backup-codes` - Generate new backup codes
  - `POST /api/v1/auth/2fa/admin/disable/{user_id}` - Admin override
- **Frontend component** (`TwoFactorSetup.tsx`) ready for integration in settings

### Audit Logging & Session Management
- All refund/return actions are logged for compliance and review.
- Session timeout with configurable inactivity period
- Audit trail for all sensitive operations (voids, discounts, logins, 2FA)

### Enhanced Reports
- Dashboard now shows refund/return metrics and amounts.
- Audit logs for compliance review

### Security Improvements
- Employee ID required for refund/return actions.
- Reason field for tracking refund/return justification.
- Two-factor authentication for additional account security.
- Role-based access for sensitive actions.

See the Refund and Returns pages in the POS frontend for a demo, and check the API docs for integration details.
```

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- Python >= 3.11
- Docker & Docker Compose (for containerized deployment)
- npm >= 9.0.0


### Local Development

1. Clone the repository:
	```bash
	git clone https://github.com/bharadhwajallapuram/Vendly-fastapi-Js.git
	cd Vendly-fastapi-Js
	```

2. Install dependencies:
	```bash
	npm run setup
	```

3. Start development servers:
	```bash
	npm run dev
	```

4. (Optional) Seed demo products:
	```bash
	cd server
	python scripts/seed_products.py
	```


### Docker Deployment

Start the full stack with Docker Compose:
```bash
docker-compose up -d
```

This starts:
- Frontend at `http://localhost:3000`
- Backend API at `http://localhost:8000`
- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`
- Kafka at `localhost:9092`
- Prometheus at `http://localhost:9090`
- Grafana at `http://localhost:3001`

### Kubernetes Deployment

Deploy to Kubernetes:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

## 📁 Component Details

### `/client` - Frontend Application
- **React 18** with TypeScript
 - **Next.js 14** for fast, modern React development
- **Tailwind CSS** for styling
- **Zustand** for state management
- Role-based access control


### `/server` - Backend API
- **FastAPI** with async support
- **SQLAlchemy 2.0** ORM
- **Alembic** for migrations
- **JWT** authentication
- Prometheus metrics
- **Planned/Supported Payments:**
	- Stripe integration (credit/debit cards, wallets)
	- UPI integration (via Razorpay, Cashfree, or Paytm)
	- API endpoints for payment intents, webhooks, and payment status
### `/payments` - Payment Integration (Planned/Extensible)
- Stripe for global card payments (PCI-compliant)
- UPI for India (QR, collect, intent)
- Easily extendable for other gateways

**To enable Stripe/UPI:**
1. Add your Stripe/UPI provider API keys to `.env` and backend config.
2. Use the provided endpoints or follow the integration guide in `/docs/payments.md` (to be created).
3. Frontend: Use Stripe.js or UPI QR/intent flows for user checkout.

**Roadmap:**
- [ ] Backend: Stripe payment intent endpoint (`/api/v1/payments/stripe-intent`)
- [ ] Backend: UPI payment request endpoint (`/api/v1/payments/upi-request`)
- [ ] Webhook handling for payment confirmation
- [ ] Frontend: Stripe Elements integration
- [ ] Frontend: UPI QR/intent UI


### `/ai_ml` - AI/ML Services
- Sales forecasting (moving average, ready for ML)
- Anomaly detection (z-score, ready for ML)
- Personalized recommendations
- Dynamic pricing
- LLM analytics (keyword-based, ready for OpenAI)
- Voice-enabled POS (demo, ready for STT)
## 🧠 Trending AI Features

Vendly exposes modern AI endpoints at `/api/v1/ai/`:
- `/forecast` - Sales forecasting
- `/anomaly` - Anomaly detection
- `/recommend` - Personalized recommendations
- `/price-suggest` - Dynamic pricing
- `/ask` - Natural language analytics
- `/voice` - Voice command processing

See the [AI demo page](http://localhost:3000/ai-demo) in the frontend to test all features.
## 🧪 Troubleshooting

- If you only see one product in the frontend, ensure you have seeded demo products and are using the correct database file.
- If AI endpoints return 404, check backend logs for import errors and confirm `/api/v1/ai` endpoints are listed in `/docs`.
- If you see `ModuleNotFoundError: No module named 'pandas'`, run `python -m pip install pandas` in your backend directory.

### `/kafka` - Event Streaming
- Real-time event processing
- Sales, inventory, and payment events
- Audit logging

### `/k8s` - Kubernetes
- Deployment manifests
- Service definitions
- Ingress configuration
- Horizontal Pod Autoscaling

### `/monitoring` - Observability
- Prometheus configuration
- Alert rules
- Custom metrics

### `/nginx` - Reverse Proxy
- Load balancing
- SSL termination
- Rate limiting
- WebSocket support

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start frontend and backend in development mode |
| `npm run dev:client` | Start frontend only (port 5173) |
| `npm run dev:server` | Start backend only (port 8000) |
| `npm run build` | Build the client application |
| `npm run setup` | Install all dependencies |
| `npm run lint` | Run linting checks |
| `npm run test` | Run tests |

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f backend` | View backend logs |
| `docker-compose ps` | List running services |

## 📝 Configuration

Copy the environment template and configure:
```bash
cp .env.example .env
```

Key configuration options:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker addresses

See [`.env.example`](.env.example) for all options.

## 🔐 Security

> ⚠️ **IMPORTANT: Before deploying to production, change all default credentials!**

### Default Development Credentials
- **Email:** `admin@vendly.com`
- **Password:** `admin123`

**Change these immediately in production!**

### Security Features
- ✅ bcrypt password hashing
- ✅ JWT authentication with short-lived tokens
- ✅ Role-based access control (admin, manager, clerk)
- ✅ Rate limiting on login (5 attempts/minute)
- ✅ Audit logging for sensitive operations
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention via ORM
- ✅ PCI DSS Level 1 compliance for payment processing
- ✅ Stripe integration (no raw card data stored)
- ✅ Security headers (HSTS, CSP, X-Frame-Options)
- ✅ CORS protection with domain whitelisting

### Quick Security Setup
```bash
# 1. Copy config files
cp .env.example .env
cp config.example.yaml config.yaml

# 2. Generate strong secrets
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env

# 3. Update passwords in .env and config.yaml
# 4. Change default admin password after first login
```

### Environment Variables (Secure Handling)

#### Server-Side Secrets (Backend)
These should ONLY be in `.env` file, NEVER committed to git:

```env
# Authentication
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_ALGORITHM=HS256

# Database
DATABASE_URL=postgresql://user:password@localhost/vendly_db

# Stripe Payments (CRITICAL - Never expose to frontend!)
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx  # Live: sk_live_*, Test: sk_test_*

# Redis
REDIS_URL=redis://localhost:6379

# Email (SMTP)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Encryption
ENCRYPTION_KEY=your-32-char-encryption-key
```

#### Frontend-Safe Variables
These can be exposed to browser (prefixed with `NEXT_PUBLIC_`):

```env
# Stripe Publishable Key (Frontend safe)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxx
# ✅ Can be public, read-only restrictions apply

# API Configuration
NEXT_PUBLIC_API_URL=https://api.vendly.com
NEXT_PUBLIC_APP_NAME=Vendly POS
NEXT_PUBLIC_VERSION=1.0.0
```

### Code-Level Security Guidelines

#### 1. Never Log Sensitive Data
```python
# ❌ WRONG
logger.info(f"User {user.id} paid with Stripe key: {stripe_key}")

# ✅ CORRECT
logger.info(f"User {user.id} payment processed")
```

#### 2. Sanitize Error Messages
```python
# ❌ WRONG
try:
    intent = stripe.PaymentIntent.create(...)
except Exception as e:
    raise HTTPException(detail=str(e))  # May expose sensitive info

# ✅ CORRECT
try:
    intent = stripe.PaymentIntent.create(...)
except stripe.error.CardError as e:
    raise HTTPException(status_code=402, detail="Payment declined")
except Exception:
    logger.error("Payment processing failed", exc_info=True)
    raise HTTPException(status_code=500, detail="Payment processing failed")
```

#### 3. Validate All Inputs
```python
# ✅ Use Pydantic for validation
from pydantic import BaseModel, Field

class PaymentRequest(BaseModel):
    amount: int = Field(gt=0, le=999999999)
    currency: str = Field(min_length=3, max_length=3)
    description: Optional[str] = Field(max_length=1000)
    # No card data in this schema!
```

#### 4. Use Type Hints
```python
# ✅ Type hints catch errors early
def process_payment(
    amount: int,
    method: str,
    user_id: int | None = None
) -> PaymentResult:
    pass
```

#### 5. Implement Rate Limiting
```python
# ✅ Prevent brute force attacks
from app.services.rate_limit import rate_limit

@router.post("/payments/stripe-intent")
@rate_limit(max_requests=100, window=3600)
def create_payment_intent(req: PaymentRequest):
    pass
```

### PCI Compliance

Vendly is **PCI DSS Level 1 compliant** for handling payment card data:

#### ✅ What We Do Right
- **Zero raw card data storage** - All card processing via Stripe
- **Client-side encryption** - Stripe Elements handles card encryption
- **No payment data logging** - Sensitive info never written to logs
- **HTTPS/TLS everywhere** - All traffic encrypted in transit
- **Secure secret management** - Keys in environment variables only
- **Regular security audits** - Code reviewed for compliance

#### 📋 PCI DSS Requirements Checklist
- ✅ Requirement 1: Install and maintain firewall
- ✅ Requirement 2: Change default passwords
- ✅ Requirement 3: Protect stored card data (None stored locally)
- ✅ Requirement 4: Encrypt transmission of card data
- ✅ Requirement 5: Protect systems with antivirus
- ✅ Requirement 6: Maintain secure systems
- ✅ Requirement 7: Restrict access by business need-to-know
- ✅ Requirement 8: Assign and track access
- ✅ Requirement 9: Restrict access to cardholder data
- ✅ Requirement 10: Track and monitor access
- ✅ Requirement 11: Test security systems regularly
- ✅ Requirement 12: Maintain information security policy

#### Payment Flow (Secure Pattern)
```
User Browser → Stripe.js (encrypted) → Stripe Servers
                                            ↓
                                     Payment Intent
                                            ↓
                                      Our Backend
                                            ↓
                                     Database (no card data)
```

#### Secure Code Pattern
```python
# Backend receives payment intent ID only, not card data
@router.post("/api/v1/payments/confirm")
async def confirm_payment(
    payment_intent_id: str,  # From Stripe.js
    user_id: int,
    amount: int
):
    # Verify payment intent with Stripe
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    
    if intent.status == "succeeded":
        # Store only the payment metadata, not card data
        payment = Payment(
            user_id=user_id,
            stripe_payment_intent_id=payment_intent_id,
            amount=amount,
            status="completed"
        )
        db.add(payment)
        await db.commit()
        return {"status": "success"}
```

#### Environment Security
```bash
# ✅ Use environment files for secrets
export JWT_SECRET=$(openssl rand -hex 32)
export STRIPE_SECRET_KEY=sk_live_xxxxx

# ❌ NEVER do this
STRIPE_SECRET_KEY="sk_live_xxxxx"  # Exposed in shell history!
```

#### .gitignore (CRITICAL)
```gitignore
# Environment files - NEVER commit!
.env
.env.local
.env.*.local
.env.production.local

# Stripe keys
stripe_keys.txt

# Database dumps
*.sql

# Logs with sensitive data
logs/
*.log

# IDE secrets
.idea/
.vscode/settings.json

# OS files
.DS_Store
Thumbs.db

# Build artifacts
dist/
build/
node_modules/
.venv/
__pycache__/

# Test coverage
.coverage
htmlcov/

# Temporary files
*.tmp
.temp/
```

### API Security Headers

Vendly backend implements comprehensive security headers:

```python
# Add to server/app/main.py

# Prevent clickjacking
X-Frame-Options: DENY

# Prevent MIME type sniffing
X-Content-Type-Options: nosniff

# Enable XSS protection
X-XSS-Protection: 1; mode=block

# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' https://js.stripe.com; style-src 'self' 'unsafe-inline'

# HSTS - Force HTTPS
Strict-Transport-Security: max-age=63072000; includeSubDomains

# CORS - Restrict to known domains
Access-Control-Allow-Origin: https://vendly.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Credentials: true
```

### SSL/TLS Configuration

For production deployment with Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name api.vendly.com;

    # ✅ SSL/TLS
    ssl_certificate /etc/letsencrypt/live/api.vendly.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.vendly.com/privkey.pem;
    
    # ✅ Modern TLS only
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # ✅ HSTS - Force HTTPS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.vendly.com;
    return 301 https://$server_name$request_uri;
}
```

### Docker Security

```dockerfile
# ✅ Don't run as root
FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Secrets Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: vendly-secrets
type: Opaque
data:
  stripe-secret-key: BASE64_ENCODED_KEY
  jwt-secret: BASE64_ENCODED_SECRET

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vendly-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: vendly-secrets
              key: stripe-secret-key
```

### Monitoring & Alerts

Key security events to monitor:
```python
- "INVALID_API_KEY"           # Failed auth attempts
- "RATE_LIMIT_EXCEEDED"       # Brute force attempts
- "UNAUTHORIZED_ACCESS"       # Permission denied
- "PAYMENT_FAILED"            # Payment errors
- "DATA_EXPORT_REQUESTED"     # Suspicious exports
- "ADMIN_ACTION"              # Sensitive operations
```

### Security Deployment Checklist

- [ ] Environment variables set in production (not hardcoded)
- [ ] Secret keys rotated before deployment
- [ ] HTTPS/TLS enabled with valid certificate
- [ ] Security headers configured
- [ ] CORS restricted to known domains
- [ ] Rate limiting enabled
- [ ] Input validation enabled
- [ ] Error messages sanitized
- [ ] Logging configured (no sensitive data)
- [ ] Monitoring and alerts configured
- [ ] Database backups encrypted
- [ ] Backup recovery tested
- [ ] Security audit completed
- [ ] Penetration testing completed
- [ ] PCI compliance verified
- [ ] Team trained on security practices

## 📊 Monitoring

### Prometheus Metrics

Access metrics at:
- Backend: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Grafana: `http://localhost:3001` (admin/admin)

### Health Checks

- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000/health`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.