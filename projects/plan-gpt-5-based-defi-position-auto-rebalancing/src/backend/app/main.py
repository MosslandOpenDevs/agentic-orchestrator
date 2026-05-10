from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
import logging
import os
import asyncio
from websockets import connect
from websockets.exceptions import ConnectionClosedOK
import json
import time
import gevent
from gevent import monkey
monkey.patch_all()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="NFT Rebalancing Platform",
    description="A platform for rebalancing NFT portfolios using a GPT-5 oracle.",
    version="0.1",
)

# CORS Configuration
origins = [
    "http://localhost:8000",  # Adjust as needed
    "http://localhost:3000",  # Adjust as needed
    "*"  # For development only - consider restricting in production
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Data Models
class RebalanceRequest(BaseModel):
    asset_ids: list[str]
    target_allocation: dict

class PredictionResponse(BaseModel):
    asset_id: str
    predicted_value: float
    confidence: float


# Dummy Smart Contract Interaction (Replace with actual smart contract logic)
def interact_with_smart_contract(asset_ids, target_allocation):
    """Simulates interaction with a smart contract for rebalancing."""
    logging.info(f"Simulating smart contract interaction: {asset_ids}, {target_allocation}")
    # In a real implementation, this would call the smart contract.
    # For now, we just return a dummy prediction.
    return {asset_id: 100.0 for asset_id in asset_ids} # Dummy prediction


# CoinGecko Integration
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY")
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

def get_nft_prices(asset_ids):
    """Retrieves NFT prices from CoinGecko."""
    try:
        prices = {}
        for asset_id in asset_ids:
            url = f"{COINGECKO_API_URL}/simple/price?ids={asset_id}&vs_currencies=usd"
            response = gevent.getrequest(url, timeout=10)
            data = json.loads(response.read().decode())
            if "usd" in data:
                prices[asset_id] = data["usd"]
            else:
                logging.warning(f"Could not retrieve price for {asset_id} from CoinGecko.")
        return prices
    except Exception as e:
        logging.error(f"Error fetching NFT prices from CoinGecko: {e}")
        raise


# OpenAI Integration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

def query_gpt5_oracle(asset_id):
    """Queries the GPT-5 oracle for NFT value prediction."""
    try:
        prompt = f"Predict the value of {asset_id} based on current market conditions and historical data."
        # Replace with actual OpenAI API call
        # response = openai.Completion.create(
        #     engine=OPENAI_MODEL,
        #     prompt=prompt,
        #     max_tokens=50
        # )
        # return response.choices[0].text.strip()
        return float(f"{asset_id} - 100.0") # Dummy prediction
    except Exception as e:
        logging.error(f"Error querying GPT-5 oracle for {asset_id}: {e}")
        raise


# WebSocket Server Integration
WS_URL = "ws://localhost:8765"  # Replace with your WebSocket server URL

async def send_rebalancing_request(asset_ids, target_allocation):
    """Sends a rebalancing request to the WebSocket server."""
    try:
        async with connect(WS_URL) as websocket:
            data = {
                "type": "rebalance",
                "asset_ids": asset_ids,
                "target_allocation": target_allocation
            }
            await websocket.send(json.dumps(data))
            response = await websocket.recv()
            logging.info(f"Received response from WebSocket server: {response}")
    except ConnectionClosedOK:
        logging.info("WebSocket connection closed normally.")
    except Exception as e:
        logging.error(f"Error sending rebalancing request to WebSocket server: {e}")


# Health Check Endpoint
@app.get("/health")
def health_check():
    """Returns a 200 OK status if the application is running."""
    return {"status": "ok"}


# API Routes
@app.post("/rebalance", response_model=PredictionResponse)
def rebalance(request: RebalanceRequest):
    """Rebalances NFT portfolio based on GPT-5 predictions."""
    asset_ids = request.asset_ids
    target_allocation = request.target_allocation

    # 1. Get NFT Prices from CoinGecko
    try:
        prices = get_nft_prices(asset_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve NFT prices from CoinGecko: {e}")

    # 2. Query GPT-5 Oracle for Predictions
    predictions = {}
    for asset_id in asset_ids:
        try:
            prediction = query_gpt5_oracle(asset_id)
            predictions[asset_id] = prediction
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get prediction from GPT-5 oracle for {asset_id}: {e}")

    # 3. Interact with Smart Contract
    smart_contract_data = interact_with_smart_contract(asset_ids, target_allocation)

    # Combine predictions and smart contract data (simplified)
    combined_data = {}
    for asset_id in asset_ids:
        combined_data[asset_id] = smart_contract_data[asset_id]

    return PredictionResponse(asset_id=asset_ids[0], predicted_value=combined_data[asset_ids[0]], confidence=0.5) # Dummy response


@app.get("/example")
def example_route():
    return {"message": "This is an example endpoint"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)