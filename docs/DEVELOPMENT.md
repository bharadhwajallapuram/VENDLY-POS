# Development Guide

## Getting Started

### Prerequisites

- Node.js >= 18.0.0
- Python >= 3.8
- PostgreSQL >= 13
- Redis >= 6.0

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bharadhwajallapuram/Vendly-fastapi-Js.git
   cd vendly
   ```

2. **Install dependencies:**
   ```bash
   npm run setup
   ```

3. **Set up environment variables:**
   
   Copy the example files and configure:
   ```bash
   cp client/.env.example client/.env
   cp server/.env.example server/.env
   ```

4. **Database setup:**
   ```bash
   # Create database
   createdb vendly_dev
   
   # Run migrations
   cd server
   alembic upgrade head
   ```

5. **Start development servers:**
   ```bash
   npm run dev
   ```

## Project Structure

```
vendly/
├── client/                 # React frontend
│   ├── src/
│   │   ├── app/           # Route pages
│   │   ├── components/    # Reusable components
│   │   ├── lib/          # Utilities and API client
│   │   └── store/        # State management
│   ├── public/           # Static assets
│   └── package.json
├── server/                # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality
│   │   ├── db/           # Database models
│   │   └── services/     # Business logic
│   ├── requirements.txt
│   └── pyproject.toml
├── shared/                # Shared types and utilities
├── docs/                 # Documentation
├── scripts/              # Build and deployment scripts
└── .github/              # CI/CD workflows
```

## Development Workflow

### Frontend Development

1. **Start development server:**
   ```bash
   npm run dev:client
   ```

2. **Code style and quality:**
   ```bash
   npm run lint:client
   npm run type-check
   ```

3. **Testing:**
   ```bash
   npm run test:client
   npm run test:coverage
   ```

### Backend Development

1. **Start development server:**
   ```bash
   npm run dev:server
   ```

2. **Code formatting:**
   ```bash
   cd server
   black .
   isort .
   ```

3. **Type checking:**
   ```bash
   mypy .
   ```

4. **Database migrations:**
   ```bash
   # Create new migration
   alembic revision --autogenerate -m "Description"
   
   # Apply migrations
   alembic upgrade head
   ```

### Shared Types

When adding new types or utilities:

1. **Add to shared package:**
   ```bash
   cd shared
   # Edit types.ts or utils.ts
   npm run build
   ```

2. **Update imports in client/server** as needed

## Code Standards

### TypeScript/React

- Use TypeScript for all new code
- Follow ESLint configuration
- Use functional components with hooks
- Implement proper error boundaries
- Add proper TypeScript types

### Python/FastAPI

- Follow PEP 8 style guidelines
- Use Black for formatting
- Add type hints to all functions
- Write comprehensive docstrings
- Implement proper error handling

### Git Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/feature-name
   ```

2. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push and create PR:**
   ```bash
   git push origin feature/feature-name
   ```

### Commit Message Convention

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance

## Testing

### Frontend Testing

- **Unit tests:** Components and utilities
- **Integration tests:** API interactions
- **E2E tests:** User workflows

### Backend Testing

- **Unit tests:** Individual functions
- **Integration tests:** API endpoints
- **Database tests:** Model operations

## Debugging

### Frontend

- Use React DevTools
- Browser network tab for API calls
- Console logging with proper levels

### Backend

- Use debugger or print statements
- Check FastAPI automatic docs at `/docs`
- Monitor logs for errors

## Performance

### Frontend

- Use React.memo for expensive components
- Implement proper loading states
- Optimize bundle size with code splitting

### Backend

- Use database indexes appropriately
- Implement caching with Redis
- Use async/await for I/O operations

## Deployment

See the deployment guide for production setup instructions.