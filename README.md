# Vendly POS - Modern Point of Sale System

Enterprise-grade POS built with **Next.js 14** (Frontend) + **FastAPI** (Backend) + **AI/ML** forecasting.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+, Python 3.11+
- Docker & Docker Compose

### Local Setup
```bash
git clone <repo> && cd Vendly-fastapi-Js

# Frontend
cd client && npm install && npm run dev
# → http://localhost:3000

# Backend (new terminal)
cd server && pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# → http://localhost:8000
# → API Docs: http://localhost:8000/docs
```

### Docker
```bash
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 📋 Key Features

| Feature | Status |
|---------|--------|
| **POS Operations** | ✅ Sale, refund, return, barcode scanning |
| **Inventory** | ✅ Real-time sync, low-stock alerts, WebSocket |
| **Users** | ✅ Role-based access (Admin, Manager, Cashier) |
| **Two-Factor Auth** | ✅ TOTP authentication with backup codes |
| **Tax Management** | ✅ GST/VAT for 8+ regions, compound taxes |
| **AI Forecasting** | ✅ Demand prediction, inventory optimization |
| **Reports** | ✅ Sales, revenue, refunds, tax reports |
| **Legal Docs** | ✅ Document versioning, GDPR consent tracking |
| **Payments** | ✅ Stripe, UPI, Cash, Card support |
| **Health Checks** | ✅ Kubernetes-ready, Prometheus metrics |
| **Backups** | ✅ Automated daily cloud backups |
| **Printers** | ✅ Thermal/Network, ESC/POS, barcode generation |

## 🏗️ Architecture

```
Frontend (Next.js 14)
       ↓ REST API + WebSocket
Backend (FastAPI)
       ↓
SQLite/PostgreSQL → Redis Cache → Kafka Events
       ↓
Monitoring: Prometheus → Grafana + Sentry
```

## 📁 Project Structure

```
.
├── client/                # Next.js frontend (React, TypeScript, Tailwind)
│   ├── src/app/          # Page routes
│   ├── src/components/   # Reusable components
│   └── src/lib/          # API clients, utilities
├── server/               # FastAPI backend
│   ├── app/api/         # API endpoints
│   ├── app/services/    # Business logic
│   ├── app/db/          # Database models
│   └── tests/           # Test suite
├── ai_ml/               # ML services (forecasting, anomaly detection)
├── shared/              # Shared types
├── docker-compose.yml   # Container orchestration
└── README.md            # This file
```

## 🔐 Authentication & Authorization

### Login Flow
1. Email + password
2. Backend validates, returns JWT + TOTP secret
3. 6-digit TOTP code verification
4. JWT stored in HTTP-only cookie

### Roles
- **Admin**: Full system access
- **Manager**: Inventory, products, reports, forecasts
- **Cashier**: POS operations only

### Default Credentials (Dev Only - Change in Production!)
```
Email: admin@vendly.com
Password: admin123
```

## 💰 Tax Management

Supports: **India** (GST), **Australia** (GST), **New Zealand** (GST), **Singapore** (GST), **UK** (VAT), **EU** (VAT), **Canada** (HST/PST), **USA** (Sales Tax)

### Example: India GST
```
Product: $100
GST (18%): $18 (CGST: $9, SGST: $9)
Total: $118
```

## 📊 AI Demand Forecasting

**Access**: `/forecasts` page or in Reports

**How it works**:
1. Select product
2. Choose forecast period (7/14/30/90 days)
3. Click "Generate Forecast"
4. View predictions with confidence intervals

**Models**: Ensemble (fast), Prophet (seasonal), ARIMA (statistical)

**Output**: Daily predictions, confidence bounds, MAPE accuracy

## 📈 Reports & Analytics

- Sales summary (total, average, by date)
- Top products (by quantity & revenue)
- Refunds & returns tracking
- Tax breakdown by region
- Demand forecasts

## 🛒 POS Workflow

### Sale
1. Scan barcode / search product
2. Add quantity & discount
3. System calculates tax
4. Select payment method
5. Print receipt
6. Inventory updated in real-time

### Refund
1. Select transaction
2. Choose items to refund
3. Confirm reason & amount
4. Payment reversed
5. Inventory restored

## 🔄 Real-Time Features

**WebSocket Endpoints**:
- `ws://localhost:8000/ws/inventory` - Stock updates
- `ws://localhost:8000/ws/sales` - Transaction events
- `ws://localhost:8000/ws/notifications` - System alerts

## 🧪 Testing

```bash
# Backend
cd server && pytest tests/ -v

# Frontend
cd client && npm test
```

## 🚢 Production Deployment

### Quick Setup
```bash
# Generate secrets
openssl rand -hex 32  # Run 4 times

# Configure environment
cp .env.production .env.production.local
nano .env.production.local  # Insert secrets

# Validate
python scripts/validate_env.py --env .env.production.local

# Deploy
bash scripts/deploy.sh
```

### Environment Variables (Critical)
```env
DATABASE_URL=postgresql://user:pass@host/db
JWT_SECRET=<random-32-chars>
STRIPE_SECRET_KEY=sk_live_xxxxx
REDIS_PASSWORD=<random>
```

### Health Check
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## 📡 Monitoring

- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3001 (dashboards, admin/admin)
- **Sentry**: https://sentry.io (error tracking)
- **API Docs**: http://localhost:8000/docs (Swagger)

## 🔧 Development

### Add API Endpoint
```python
# server/app/api/v1/routers/products.py
@router.get("/")
async def list_products():
    return await ProductService.list()
```

### Add Database Model
```python
# server/app/db/models.py
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
```

### Create Migration
```bash
cd server
alembic revision --autogenerate -m "Add field"
alembic upgrade head
```

### Add Frontend Component
```tsx
// client/src/components/MyComponent.tsx
'use client';
import { useState } from 'react';

export default function MyComponent() {
  return <div>Content</div>;
}
```

## 🌐 API Endpoints

### Core Endpoints
```
POST   /api/v1/auth/login              User login
POST   /api/v1/auth/logout             User logout
GET    /api/v1/sales                   List sales
POST   /api/v1/sales                   Create sale
POST   /api/v1/sales/{id}/refund       Refund sale
GET    /api/v1/products                List products
POST   /api/v1/inventory/adjust        Update stock
GET    /api/v1/reports/summary         Sales report
POST   /api/v1/ai/forecast             Generate forecast
```

**Full API Docs**: http://localhost:8000/docs

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Check database ready
docker-compose ps | grep postgres

# Check PYTHONPATH
export PYTHONPATH=/path/to/Vendly-fastapi-Js
```

### Frontend Compilation Errors
```bash
# Clear cache
rm -rf client/.next node_modules
npm install
npm run dev
```

### Database Issues
```bash
# Reset (dev only)
rm vendly.db

# Migrate
cd server && alembic upgrade head

# Seed demo data
python scripts/seed_products.py
```

### Port in Use
```bash
# Find process
lsof -i :3000

# Kill it
kill -9 <PID>

# Or use different port
npm run dev -- -p 3001
```

## 📚 Documentation

- **Architecture**: See project structure above
- **Security**: Role-based access, JWT, TOTP 2FA, PCI DSS compliant
- **API**: http://localhost:8000/docs (interactive Swagger UI)
- **Configuration**: Copy `.env.example` to `.env` and configure

## 🚀 Available Commands

```bash
npm run dev              # Start frontend + backend
npm run dev:client       # Frontend only
npm run dev:server       # Backend only
npm run build            # Build client
npm run setup            # Install all dependencies
npm run lint             # Run linting
npm run test             # Run tests

# Docker
docker-compose up -d     # Start all services
docker-compose down      # Stop services
docker-compose logs -f   # View logs
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/name`
3. Commit: `git commit -m "feat: description"`
4. Push: `git push origin feature/name`
5. Open Pull Request

**Code Style**:
- Python: PEP 8 (use `black`, `flake8`)
- TypeScript: ESLint
- Commits: Conventional commits (feat:, fix:, docs:)

## 🔐 Security

### Default Credentials (Change immediately!)
```
Email: admin@vendly.com
Password: admin123
```

### Security Features
- ✅ JWT authentication (HS256)
- ✅ Two-factor authentication (TOTP)
- ✅ Password hashing (bcrypt)
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Rate limiting (login, API)
- ✅ CORS protection
- ✅ Security headers (HSTS, CSP)
- ✅ PCI DSS Level 1 (Stripe integration)
- ✅ Audit logging

### Reporting Security Issues
⚠️ Do NOT open public issues for security vulnerabilities.

Email: security@vendly.app with:
- Vulnerability description
- Affected components
- Proof of concept
- Impact assessment

## 📄 License

MIT License - see LICENSE file

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: See this README
- **API Docs**: http://localhost:8000/docs
- **Email**: support@vendly.app

## 📊 Changelog

### v2.1.0 (December 2025)
- ✅ AI demand forecasting dashboard (fully integrated)
- ✅ Improved tax reporting
- ✅ WebSocket real-time inventory
- ✅ Enhanced error handling

### v2.0.0 (November 2025)
- ✅ Tax management (GST/VAT for 8+ regions)
- ✅ Legal documents with versioning
- ✅ Two-factor authentication (TOTP)
- ✅ Refund/return workflows
- ✅ Kubernetes support
- ✅ Comprehensive monitoring

### v1.0.0 (October 2025)
- ✅ Core POS functionality
- ✅ Inventory management
- ✅ Reports & analytics
- ✅ User management
- ✅ Role-based access

---

**Made with ❤️ for modern retail**

**Author**: Bharadhwaj Reddy Allapuram  
Last Updated: December 2025 | Version: 2.1.0 | Status: Production-Ready ✅
