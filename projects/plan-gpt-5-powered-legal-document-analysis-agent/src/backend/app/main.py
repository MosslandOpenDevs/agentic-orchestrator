from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestException
from typing import List
import os
import logging
import asyncio
import websockets
from websockets import WebSocketServer
from websockets import WebSocketClient
import json
import coingecko
import openai
import time

app = FastAPI(
    title="Mossland NFT Valuation Engine",
    description="A FastAPI application for NFT valuation and portfolio optimization.",
    version="0.1",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Environment variable configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "YOUR_COINGECKO_API_KEY")
WS_PORT = int(os.environ.get("WS_PORT", 8765))

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Health Check Endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}


# Example NFT Data (Replace with Web3.js integration)
nft_data = [
    {"name": "NFT A", "rarity": 0.1, "sales_history": [100, 150, 120]},
    {"name": "NFT B", "rarity": 0.05, "sales_history": [80, 90, 70]},
]


# Coingecko API Integration
def get_crypto_price(symbol):
    try:
        client = coingecko.Client(api_version='experimental')
        ticker = client.get_ticker(symbol=symbol)['ticker'][0]
        return ticker['last']
    except Exception as e:
        logging.error(f"Error fetching crypto price for {symbol}: {e}")
        return None


# GPT-5 Prompt Engineering (Placeholder)
def generate_nft_valuation(nft_data):
    prompt = f"""
    Analyze the following NFT data and provide a valuation estimate.
    Rarity: {nft_data['rarity']}
    Sales History: {nft_data['sales_history']}
    Consider current market conditions and overall trends.
    Return only the valuation in USD.
    """
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"Error generating NFT valuation: {e}")
        return None


# Portfolio Risk Calculation
def calculate_portfolio_risk(valuations):
    # Placeholder - Implement actual risk calculation logic here
    total_value = sum(float(v) for v in valuations)
    return total_value  # Simple example


# Portfolio Optimization Recommendations (Placeholder)
def generate_portfolio_recommendations(valuations):
    # Placeholder - Implement actual recommendation logic here
    recommendations = ["Hold your NFTs", "Consider diversifying"]
    return recommendations


# Risk Scoring System
def calculate_risk_score(valuations):
    # Placeholder - Implement actual risk scoring logic here
    total_value = sum(float(v) for v in valuations)
    return total_value  # Simple example


# Alert Generation
def generate_alerts(valuations):
    alerts = []
    for i, valuation in enumerate(valuations):
        try:
            price = get_crypto_price(nft_data[i]['name'].lower())
            if price is not None:
                change = (float(valuation) - price) / price
                if abs(change) > 0.05:  # 5% threshold
                    alerts.append(f"NFT {nft_data[i]['name']} value has dropped by {change * 100:.2f}%")
        except Exception as e:
            logging.error(f"Error generating alert for {nft_data[i]['name']}: {e}")
    return alerts


# WebSocket Server
async def websocket_handler(websocket, path):
    try:
        logging.info("Client connected")
        await websocket.accept()
        while True:
            message = await websocket.recv()
            logging.info(f"Received: {message}")
            # Process message and send response
            response = f"Server received: {message}"
            await websocket.send(response)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        logging.info("Client disconnected")


async def run_websocket_server():
    await websocket_server.serve_async(("", WS_PORT))


# Initialize WebSocket Server
websocket_server = WebSocketServer(run_websocket_server)


# API Routes
@app.get("/nft-valuation/{nft_name}", response_model=dict)
async def nft_valuation(nft_name: str):
    nft = next((item for item in nft_data if item["name"] == nft_name), None)
    if not nft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NFT not found")

    valuation = generate_nft_valuation(nft)
    if valuation is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate valuation")

    portfolio_risk = calculate_portfolio_risk([valuation])
    recommendations = generate_portfolio_recommendations([valuation])
    risk_score = calculate_risk_score([valuation])
    alerts = generate_alerts([valuation])

    return {
        "nft_name": nft_name,
        "valuation": valuation,
        "portfolio_risk": portfolio_risk,
        "recommendations": recommendations,
        "risk_score": risk_score,
        "alerts": alerts
    }


@app.get("/example")
async def example():
    return {"message": "This is an example endpoint"}


if __name__ == "__main__":
    asyncio.run(run_websocket_server())
    # Replace "0.0.0.0" with "127.0.0.1" for local testing
    # Replace 8000 with the desired port
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)