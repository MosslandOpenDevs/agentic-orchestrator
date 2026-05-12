from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import Dict
from datetime import datetime
import logging
import os
import uvicorn
from uvicorn.middleware import Middleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from .routers import api_router
from .health import health_check
from .config import Settings

app = FastAPI(
    title="Mossland Smart Contract Security Platform",
    description="A platform to reduce smart contract vulnerabilities and accelerate development.",
    version="0.1.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Environment Variable Configuration
settings = Settings()
app.state.settings = settings

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.exception(exc)
    return (
        exc.status_code,
        {"message": "Internal Server Error"},
    )

# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    # Initialize any necessary resources here
    # Example:  settings.openai_api_key = os.environ.get("OPENAI_API_KEY")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
    # Perform cleanup tasks here
    # Example:  await openai.close()


# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# API Router
app.include_router(api_router)

# Static Files (for serving frontend assets)
static_files = StaticFiles(directory="static", html=True)
app.mount("/static", static_files, name="static")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=True,
        workers=4,
        ssl_certificate=settings.ssl_certificate,
        ssl_key=settings.ssl_key,
    )