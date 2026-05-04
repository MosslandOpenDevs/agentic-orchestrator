from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
import os
from .database import Database
from .exceptions import DatabaseError, APIError
from .health import health_check
from .router import router

app = FastAPI(
    title="Rain Stablecoin Analytics",
    description="A platform for analyzing Rain stablecoin data and DeFi trends.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Configure CORS
origins = [
    "http://localhost:8000",  # React development server
    "http://localhost:3000",  # React development server
    "http://localhost:8080",  # Example backend
    "*"  # Allow all origins for development - REMOVE FOR PRODUCTION
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment Variable Configuration
if not os.environ.get("DATABASE_URL"):
    logger.error("DATABASE_URL environment variable not set.")
    raise EnvironmentError("DATABASE_URL environment variable must be set.")

if not os.environ.get("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY environment variable not set.")
    raise EnvironmentError("OPENAI_API_KEY environment variable must be set.")

# Database Dependency
def get_database():
    db = Database(os.environ["DATABASE_URL"])
    return db

# Exception Handlers
@app.exception_handler(DatabaseError)
def database_exception_handler(exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exception)},
    )

@app.exception_handler(APIError)
def api_exception_handler(exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exception)},
    )

# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete.")
    health_check()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown complete.")

# Health Check Endpoint
@app.get("/health")
async def health_check_endpoint():
    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
    )

# API Router
app.include_router(router)

@app.get("/test")
async def test_endpoint():
    return {"message": "Hello from Rain Stablecoin Analytics!"}