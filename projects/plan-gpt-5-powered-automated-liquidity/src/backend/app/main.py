from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
import logging
import os
import asyncio
import websockets
from typing import Dict, Any
from datetime import datetime

app = FastAPI(
    title="NFT Trading Platform",
    description="A platform for trading NFTs using Billions Network and AI analysis.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:8080",  # Replace with your frontend URL
    "http://localhost:3000",
    "http://localhost:3001",
    "https://localhost:8080",
    "https://localhost:3000",
    "https://localhost:3001",
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment variable configuration
API_KEY = os.environ.get("BILLIONS_API_KEY", "default_key")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "default_openai_key")
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "default_coingecko_key")


# Data Models
class PortfolioItem(BaseModel):
    asset_id: str
    quantity: int
    price: float


class Trade(BaseModel):
    type: str  # "buy" or "sell"
    asset_id: str
    quantity: int
    price: float


# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Dummy Data (Replace with actual database integration)
portfolios = {}
trade_history = []


# Example AI Function (Replace with OpenAI integration)
def analyze_text(text: str) -> str:
    # Simulate OpenAI analysis
    return f"AI analysis: {text}"


# Example WebSocket Server
async def websocket_handler(websocket, path):
    try:
        logger.info("WebSocket connection established")
        while True:
            message = await websocket.recv()
            logger.info(f"Received message: {message}")
            # Process the message (e.g., send to AI, update portfolio)
            response = analyze_text(message)
            await websocket.send(response)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed")


# API Routes

@app.post("/portfolio/add", response_model=PortfolioItem)
async def add_portfolio_item(item: PortfolioItem):
    if item.asset_id in portfolios:
        raise HTTPException(status_code=400, detail="Asset already in portfolio")
    portfolios[item.asset_id] = item
    logger.info(f"Added portfolio item: {item.asset_id}")
    return item


@app.post("/portfolio/remove", response_model=PortfolioItem)
async def remove_portfolio_item(item_id: str):
    if item_id not in portfolios:
        raise HTTPException(status_code=404, detail="Asset not found in portfolio")
    item = portfolios.pop(item_id)
    logger.info(f"Removed portfolio item: {item_id}")
    return item


@app.post("/trade", response_model=Trade)
async def record_trade(trade: Trade):
    trade_history.append(trade)
    logger.info(f"Recorded trade: {trade}")
    return trade


@app.get("/trade_history", response_model=list[Trade])
async def get_trade_history():
    return trade_history


@app.get("/coingecko_price/{asset_id}")
async def get_coingecko_price(asset_id: str):
    try:
        import requests
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        price = data[asset_id]["usd"]
        return {"price": price}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching price from Coingecko: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price")


# Example of using the WebSocket server
@app.get("/ws")
async def websocket_endpoint():
    ws = websockets.WebSocketServer(
        "localhost", 8765, websocket_handler)
    return {"url": f"ws://localhost:8765"}