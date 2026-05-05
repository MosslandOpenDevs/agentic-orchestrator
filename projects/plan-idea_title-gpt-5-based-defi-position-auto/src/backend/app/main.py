from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List
import logging
import os
import time
import asyncio
from datetime import datetime

# Initialize logging
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
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Environment Variable Configuration
env_vars = {
    "COINGECKO_API_KEY": os.environ.get("COINGECKO_API_KEY", "YOUR_COINGECKO_API_KEY"),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"),
    "SOLANA_RPC_URL": os.environ.get("SOLANA_RPC_URL", "https://api.solana.com"),
}

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})


# Example API Route (Placeholder)
@app.get("/api/data")
async def get_data():
    data = {
        "message": "Hello from TerraForm!",
        "timestamp": datetime.now().isoformat()
    }
    return JSONResponse(status_code=200, content=data)

# Example WebSocket Endpoint (Placeholder)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    try:
        await websocket.accept()
        while True:
            await asyncio.sleep(5)
            await websocket.send(f"Message from WebSocket: {datetime.now().isoformat()}")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close()


# Dependency for logging
def log_request(request: Request):
    request_info = {
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers),
        "client_ip": request.client.host
    }
    logging.info(f"Request: {request_info}")
    return request


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logging.exception("An error occurred:", exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Internal Server Error"},
    )


# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logging.info("TerraForm application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("TerraForm application shutdown complete.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)