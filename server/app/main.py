from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routers import api_router

app = FastAPI(
    title="Vendly POS API", 
    version="1.0.0",
    description="A modern point-of-sale system API"
)

# Configure CORS - Allow specific origins for development with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174", 
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,  # Enable credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Vendly POS API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is operational"}

app.include_router(api_router, prefix="/api/v1")