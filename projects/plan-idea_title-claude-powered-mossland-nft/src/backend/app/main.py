from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
import logging
import os
import asyncio
from typing import List

app = FastAPI(
    title="Mossland NFT Portfolio Optimizer",
    description="A platform for optimizing Mossland NFT portfolios.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8080",
    "https://your-frontend-domain.com",
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
)
logger = logging.getLogger(__name__)

# Define a simple data model
class PortfolioItem(BaseModel):
    nft_name: str
    quantity: int
    current_price: float

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

# Dummy data for demonstration
portfolio_data = [
    PortfolioItem(nft_name="Mossland", quantity=10, current_price=150.0),
    PortfolioItem(nft_name="Mossland", quantity=5, current_price=200.0),
]

# Example API endpoint
@app.get("/portfolio")
async def get_portfolio():
    return portfolio_data

# Example error handling
@app.get("/error")
async def raise_error():
    raise HTTPException(status_code=400, detail="This is an error")

# Example rate limiting (optional - requires a library like `fastapi-ratelimit`)
# from fastapi_ratelimit import RateLimit
# limiter = RateLimit(limit=3, key_func=lambda ctx: ctx.dependent().name)
# @app.get("/api/data", rate_limit=limiter)
# async def get_data():
#     return {"data": "This is some data"}

# Lifespan events (startup/shutdown)
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

# Environment variable configuration
def get_env_var(key: str):
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Environment variable '{key}' is not set.")
    return value

# Example dependency for environment variables
def get_api_key() -> str:
    api_key = get_env_var("API_KEY")
    return api_key