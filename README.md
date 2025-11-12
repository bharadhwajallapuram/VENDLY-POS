# Vendly - Professional Point of Sale System

A modern, full-stack point-of-sale system built with React, TypeScript, FastAPI, and Python.

## 🏗️ Project Structure

```
vendly/
├── client/          # React frontend application
├── server/          # FastAPI backend application  
├── shared/          # Shared types and utilities
├── docs/            # Documentation
├── scripts/         # Build and deployment scripts
├── .github/         # GitHub workflows and templates
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- Python >= 3.8
- npm >= 9.0.0

### Installation

1. Clone the repository:
```bash
git clone https://github.com/bharadhwajallapuram/Vendly-fastapi-Js.git
cd vendly
```

2. Install dependencies:
```bash
npm run setup
```

### Development

Start both frontend and backend in development mode:
```bash
npm run dev
```

Or run them separately:
```bash
# Frontend only (runs on http://localhost:5173)
npm run dev:client

# Backend only (runs on http://localhost:8000)
npm run dev:server
```

### Building

Build the client application:
```bash
npm run build
```

## 📁 Directory Details

### `/client` - Frontend Application
- React 18 with TypeScript
- Vite for fast development and building
- Tailwind CSS for styling
- Zustand for state management
- React Router for navigation

### `/server` - Backend API
- FastAPI framework
- SQLAlchemy ORM
- Alembic for database migrations
- Redis for caching
- JWT authentication

### `/shared` - Shared Code
- TypeScript type definitions
- Utility functions
- Constants and enums

### `/docs` - Documentation
- API documentation
- Development guides
- Deployment instructions

### `/scripts` - Automation Scripts
- Docker configurations
- Build scripts
- Deployment scripts

## 🛠️ Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start both client and server in development mode |
| `npm run build` | Build the client application |
| `npm run setup` | Install all dependencies |
| `npm run lint` | Run linting checks |
| `npm run test` | Run tests |
| `npm run docker:build` | Build Docker containers |
| `npm run docker:up` | Start services with Docker Compose |

## 🐳 Docker Support

Run with Docker Compose:
```bash
npm run docker:up
```

## 📝 Environment Variables

Create `.env` files in both `client` and `server` directories based on the `.env.example` templates.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.