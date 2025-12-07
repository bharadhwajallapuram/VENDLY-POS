# Vendly - Enterprise Point of Sale System

A modern, enterprise-grade point-of-sale system built with React, TypeScript, FastAPI, and Python. Designed for high availability, scalability, and real-time operations.

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
├── client/              # Next.js frontend application
├── server/              # FastAPI backend application
├── shared/              # Shared types and utilities
├── ai_ml/               # AI/ML prediction services
├── kafka/               # Event streaming configuration
├── k8s/                 # Kubernetes manifests
├── monitoring/          # Prometheus & alerting
├── nginx/               # Reverse proxy configuration
├── redis/               # Cache configuration
├── scripts/             # Build and deployment scripts
├── docker-compose.yml   # Container orchestration
├── Dockerfile           # Multi-stage build
├── config.example.yaml  # User configuration template
└── .env.example         # Environment template
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
cd vendly
```

2. Install dependencies:
```bash
npm run setup
```

3. Start development servers:
```bash
npm run dev
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
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Zustand** for state management
- Role-based access control

### `/server` - Backend API
- **FastAPI** with async support
- **SQLAlchemy 2.0** ORM
- **Alembic** for migrations
- **JWT** authentication
- Prometheus metrics

### `/ai_ml` - AI/ML Services
- Sales forecasting with Random Forest
- Inventory optimization (EOQ, reorder points)
- Anomaly detection with Isolation Forest

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