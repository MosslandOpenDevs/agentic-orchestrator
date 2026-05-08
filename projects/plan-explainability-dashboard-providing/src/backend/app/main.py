from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
import os
from datetime import datetime
from uuid import uuid4
import asyncio

app = FastAPI(
    title="Mossland Agent",
    description="Agent-based development for Mossland",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:8080",  # Adjust as needed
    "http://localhost:3000",  # Adjust as needed
    "http://localhost:8000",  # Adjust as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# Environment variable configuration
API_KEY = os.environ.get("OPENAI_API_KEY", "default_api_key")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Example API route (replace with your actual logic)
@app.get("/data")
async def get_data():
    data = {
        "message": "Hello from Mossland Agent!",
        "timestamp": datetime.now().isoformat()
    }
    return JSONResponse(content=data)


# Example exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.exception(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Internal Server Error"},
    )


# Lifespan events (startup/shutdown)
@app.on_event("startup")
async def startup_event():
    logger.info("Mossland Agent application startup")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Mossland Agent application shutdown")


# Example rate limiting (optional - requires a library like `starlette` or `fastapi-ratelimit`)
# from fastapi_ratelimit import RateLimit
# rate_limit = RateLimit(
#     key_func=lambda req: req.client.hostname,
#     limit=5,
#     period=60,
#     max_errors=3,
# )
# @app.get("/data", rate_limit=rate_limit)
# async def get_data_rate_limited():
#     data = {
#         "message": "Hello from Mossland Agent!",
#         "timestamp": datetime.now().isoformat()
#     }
#     return JSONResponse(content=data)