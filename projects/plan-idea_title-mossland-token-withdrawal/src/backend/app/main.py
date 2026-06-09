from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestException
from typing import List
import logging
import os
import asyncio
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Mossland NFT Ecosystem Management Platform",
    description="A fully autonomous, AI-powered NFT ecosystem management platform.",
    version="1.0",
)

# CORS Configuration
origins = [
    "http://localhost:8000",  # Allow requests from local development server
    "http://localhost:3000",  # Allow requests from React frontend
    "*",  # Allow requests from any origin (for production - be cautious)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["Access-Control-Allow-Origin"],
)


# Dependency for logging
def log_request(request):
    logging.info(f"Request: {request.method} {request.url}")
    return request


# Dependency for rate limiting (example - can be expanded)
async def rate_limit():
    # Placeholder for rate limiting implementation
    pass


# Health Check Endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Exception Handlers
@app.exception_handler(RequestException)
async def http_exception_handler(request, exc):
    logging.exception("An error occurred")
    return HTTPException(status_code=exc.status_code, detail="Internal Server Error")


# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logging.info("Application startup")


@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutdown")


# WebSocket Server
async def websocket_handler(websocket):
    try:
        logging.info("Client connected")
        await log_request(websocket)
        # Simulate some data processing
        await asyncio.sleep(5)
        await websocket.send("Hello from the server!")
        logging.info("Client disconnected")
    except WebSocketDisconnect:
        logging.info("Client disconnected")
    except Exception as e:
        logging.exception(f"Error in WebSocket handler: {e}")


# API Routes (Example - expand as needed)
@app.get("/nft-data/{nft_id}")
async def get_nft_data(nft_id: str):
    # Placeholder for NFT data retrieval
    return {"nft_id": nft_id, "data": "Some NFT data"}


@app.post("/nft-withdraw/{nft_id}")
async def nft_withdraw(nft_id: str):
    # Placeholder for NFT withdrawal logic
    return {"nft_id": nft_id, "status": "withdrawal initiated"}


# Environment Variable Configuration
# Example:
# os.environ["API_KEY"] = "your_api_key"
# You should use a proper method for handling environment variables in production.


# Example of a custom dependency
async def get_config():
    return {
        "api_key": os.environ.get("API_KEY", "default_api_key"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
    }


# Example usage of the custom dependency
@app.get("/config")
async def get_config_data(config: dict = Depends(get_config)):
    return config