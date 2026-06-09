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
    title="Mossland NFT Ecosystem Management",
    description="A fully autonomous, AI-powered NFT ecosystem management platform.",
    version="1.0",
)

# CORS Configuration
origins = [
    "http://localhost:8080",  # Replace with your frontend URL
    "http://localhost:3000",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Environment Variable Configuration
API_KEY = os.environ.get("API_KEY", "default_api_key")

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# WebSocket Server
ws_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    logging.info(f"WebSocket connection established with {websocket.remote_address}")

    try:
        while True:
            message = await websocket.receive_text()
            logging.info(f"Received message: {message}")
            # Process the message here (e.g., send to AI agent)
            # For demonstration, just echo the message back
            await websocket.send_text(f"Message received: {message}")
    except WebSocketDisconnect:
        logging.info(f"WebSocket connection closed by {websocket.remote_address}")
        ws_connections.remove(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

# Exception Handlers
@app.exception_handler(RequestException)
async def http_exception_handler(request, exc):
    logging.exception("An error occurred: ", exc)
    raise HTTPException(status_code=400, detail=str(exc))

# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logging.info("FastAPI application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("FastAPI application shutdown complete.")
    # Close WebSocket connections here if needed
    for ws in ws_connections:
        await ws.close()
    ws_connections = []

# Example API Route (Placeholder)
@app.get("/example")
async def example_route():
    return {"message": "This is an example API route."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)