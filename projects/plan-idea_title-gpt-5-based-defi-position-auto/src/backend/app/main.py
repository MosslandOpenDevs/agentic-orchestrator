from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
import os
import time
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="TerraForm - Mossland Auto-Rebalancing",
    description="AI-driven auto-rebalancing agent for Mossland NFT holders.",
    version="0.1.0",
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Replace with your frontend URL
    "http://localhost:8080", # Replace with your frontend URL
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variable Configuration
env_vars = {
    "COINGECKO_API_KEY": os.environ.get("COINGECKO_API_KEY"),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    "SOLANA_RPC_URL": os.environ.get("SOLANA_RPC_URL"),
    "SOLANA_NETWORK": os.environ.get("SOLANA_NETWORK", "testnet"),
}

# Dependency for environment variables
def get_env_var(key):
    if not env_vars.get(key):
        raise HTTPException(status_code=400, detail=f"Environment variable '{key}' not set.")
    return env_vars[key]

# Health Check Endpoint
@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})

# Example API Route (Replace with your actual API logic)
@app.get("/api/data")
async def get_data():
    data = {
        "message": "Hello from TerraForm!",
        "timestamp": datetime.utcnow().isoformat()
    }
    return JSONResponse(status_code=200, content=data)

# Example WebSocket Endpoint (Placeholder)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    try:
        await websocket.accept()
        # Simulate sending data every second
        while True:
            await asyncio.sleep(1)
            await websocket.send(
                "{\"message\": \"Data from WebSocket\"}"
            )
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close()

# Lifespan Events
@app.on_startup()
async def startup_event():
    logging.info("TerraForm startup complete!")

@app.on_shutdown()
async def shutdown_event():
    logging.info("TerraForm shutdown initiated.")

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logging.exception("An error occurred:", exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Internal Server Error"},
    )

# Example Rate Limiting (Placeholder - Requires a rate limiting library)
# @app.rate_limit(key="api_key", rate=10, period=60)
# async def protected_route(api_key):
#     # Your protected API logic here
#     return JSONResponse(status_code=200, content={"message": "Protected route accessed"})