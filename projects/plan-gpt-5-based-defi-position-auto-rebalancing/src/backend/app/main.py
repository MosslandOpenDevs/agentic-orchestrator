from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List
import logging
import os
import uvicorn
from datetime import datetime
from uuid import uuid4
import time
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Mossland Portfolio Analyzer",
    description="A portfolio analysis tool leveraging blockchain and AI.",
    version="0.1.0",
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Adjust as needed
    "http://localhost:3001",  # Adjust as needed
    "http://localhost:8080",  # Adjust as needed
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
    allow_credentials=True,
)


# Dependency for logging
def log_request(request: Request):
    logging.info(f"Incoming request: {request.method} {request.url}")
    return LogRequestResponseWrapper(request)


# Response wrapper for logging
class LogRequestResponseWrapper:
    def __init__(self, request: Request):
        self.request = request

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Health Check Endpoint
@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})


# Example API Route (Placeholder)
@app.get("/analyze")
def analyze_portfolio(data: dict = None):
    if data is None:
        raise HTTPException(status_code=400, detail="No data provided")
    logging.info(f"Received analysis request: {data}")
    # Simulate some processing
    time.sleep(1)
    return JSONResponse(status_code=200, content={"result": "Analysis complete"})


# Exception Handler
@app.exception_handler(HTTPException)
def http_exception_handler(exception: HTTPException):
    logging.error(f"HTTP Exception: {exception}")
    return JSONResponse(status_code=exception.status_code, content={"error": exception.detail},
                       headers={"Content-Type": "application/json"})


# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logging.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown")


# Environment Variable Configuration
def get_env_var(key: str, default: str = None):
    value = os.getenv(key, default)
    if value is None:
        logging.warning(f"Environment variable {key} not set.")
    return value


# Example Usage of Environment Variables
API_KEY = get_env_var("OPENAI_API_KEY")
COINGEKO_API_KEY = get_env_var("COINGEKO_API_KEY")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)