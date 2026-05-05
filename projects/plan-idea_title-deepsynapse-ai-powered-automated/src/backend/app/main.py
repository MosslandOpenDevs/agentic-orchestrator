from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from datetime import datetime

app = FastAPI(
    title="DTCC Tokenized Securities Platform",
    description="A platform for managing tokenized securities with DTCC integration.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:8080",  # React frontend
    "http://localhost:3000",  # React frontend
    "http://localhost:8000",  # FastAPI UI
    "*"  # Allow all origins for development - remove in production
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variable configuration
dotenv = load_dotenv()

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Dummy data for demonstration
@app.get("/data")
def get_data():
    return {"message": "This is some dummy data from the DTCC integration."}

# Example API route (replace with actual DTCC integration)
@app.get("/dtcc-data/{security_id}")
def get_dtcc_data(security_id: str):
    # Simulate fetching data from DTCC
    if security_id == "AAPL":
        return {"security_id": security_id, "price": 175.50, "timestamp": datetime.utcnow().isoformat()}
    else:
        raise HTTPException(status_code=404, detail="Security not found")

# Example API route for Coingecko
@app.get("/coingecko/{coin_id}")
def get_coingecko_data(coin_id: str):
    # Simulate fetching data from Coingecko
    if coin_id == "bitcoin":
        return {"coin_id": coin_id, "price": 65000.00, "timestamp": datetime.utcnow().isoformat()}
    else:
        raise HTTPException(status_code=404, detail="Coin not found")

# Example API route for OpenAI
@app.get("/openai/{prompt}")
def get_openai_response(prompt: str):
    # Simulate calling OpenAI API
    return {"response": f"OpenAI says: {prompt}"}

# Example API route for WebSocket
@app.get("/ws")
def get_websocket_url():
    return {"url": "ws://localhost:8081"} # Replace with actual WebSocket server URL

# Exception handlers
@app.exception_handler(HTTPException)
def http_exception_handler(exception: HTTPException):
    logger.exception_handler(exception)
    return {"detail": exception.detail}

# Lifespan events
@app.on_event("startup")
def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")

# Rate limiting (optional - example)
# from fastapi import FastAPI, Depends
# from fastapi.middleware.api import Middleware
#
# rate_limiter = RateLimiter(max_requests=10, interval=60)
#
# @app.middleware("api")
# async def rate_limit_middleware(request: Request, response: Response, *args, **kwargs):
#     if rate_limiter.wait_for(request):
#         return response
#     else:
#         raise HTTPException(status_code=429, detail="Too many requests")
from dotenv import load_dotenv