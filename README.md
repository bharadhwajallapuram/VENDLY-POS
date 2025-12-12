
# Vendly - Enterprise Point of Sale System

A modern, enterprise-grade point-of-sale system built with Next.js 14 (React/TypeScript) frontend and FastAPI (Python) backend. Includes trending AI features, real-time event processing, and robust security.

## 📚 Documentation

**For comprehensive documentation, see the [`docs/`](./docs/) folder:**
- **[Complete Documentation Index](./docs/README.md)** - Start here for all guides
- **[Offline Mode Guide](./docs/OFFLINE_MODE.md)** - Offline sales queueing & sync
- **[Granular Permissions Guide](./docs/GRANULAR_PERMISSIONS.md)** - Role-based access control

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

Vendly now supports advanced refund and return flows, plus other improvements:

- **Refunds & Returns:**
	- Partial and full refunds for sales, with inventory adjustment.
	- Returns flow for items, with employee authorization and reason logging.
	- Refund/Return endpoints: `/api/v1/sales/{sale_id}/refund` and `/api/v1/sales/{sale_id}/return`.
	- Frontend UI for refund/return in POS, with sale lookup by ID, phone, or name.
	- Refund/Return statistics in reports (total refunds, returns, amounts).
- **Audit Logging:**
	- All refund/return actions are logged for compliance and review.
- **Enhanced Reports:**
	- Dashboard now shows refund/return metrics and amounts.
- **Security:**
	- Employee ID required for refund/return actions.
	- Reason field for tracking refund/return justification.
- **Other Improvements:**
	- Improved error handling and feedback in refund/return UI.
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