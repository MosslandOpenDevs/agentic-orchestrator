from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from datetime import datetime

app = FastAPI(
    title="xBubble Valuation API",
    description="Real-time asset valuation and trading automation for the Mossland ecosystem.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# Environment Variable Configuration
COINGEKO_API_KEY = os.environ.get("COINGEKO_API_KEY", None)
if not COINGEKO_API_KEY:
    logger.warning("COINGEKO_API_KEY not set.  Using default values.")


# Health Check Endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}


# Example API Route (Replace with your actual logic)
@app.get("/assets/{asset_id}")
async def get_asset_valuation(asset_id: str):
    try:
        # Simulate fetching data from Coingecko
        # Replace with actual API call
        valuation = {
            "asset_id": asset_id,
            "price": round(float(asset_id[:2]) + (float(asset_id[2:]) * 0.1), 2),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        return valuation
    except Exception as e:
        logger.exception("Error fetching asset valuation: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch asset valuation")


@app.on_event("startup")
async def startup_event():
    logger.info("xBubble Valuation API startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("xBubble Valuation API shutdown complete.")


# Example Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exception):
    logger.exception("Exception occurred: %s", exception)
    return {"detail": str(exception)}