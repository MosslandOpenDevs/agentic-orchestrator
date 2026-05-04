from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
from pydantic import BaseModel
import logging
import os
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

app = FastAPI(
    title="Rain Stablecoin Analytics",
    description="A platform for analyzing Rain stablecoin data and providing insights.",
    version="0.1.0",
)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CORS Middleware
origins = ["http://localhost:8080", "http://localhost:3000"]  # Add your frontend origin here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Define a Pydantic model for request bodies
class PortfolioData(BaseModel):
    address: str
    nft_ids: List[str] = []

# Define a Pydantic model for response bodies
class AnalyticsResponse(BaseModel):
    data: dict

# Health Check Endpoint
@app.get("/health")
def health_check():
    return JSONResponse(status_code=200, content={"status": "ok"})

# Example API Route (Replace with your actual API logic)
@app.get("/analytics")
async def analytics(portfolio_data: PortfolioData):
    try:
        # Simulate fetching data
        # Replace this with your actual data fetching logic
        data = {
            "address": portfolio_data.address,
            "nft_ids": portfolio_data.nft_ids,
            "timestamp": datetime.now().isoformat(),
            "rain_balance": 100.0,
            "nft_value": 5000.0
        }
        return AnalyticsResponse(data=data)
    except Exception as e:
        logger.error(f"Error in analytics endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Exception Handlers
@app.exception_handler(HTTPException)
def http_exception_handler(app, e):
    logger.exception(e)
    return JSONResponse(status_code=e.status_code, content={"error": str(e)},
                      headers=e.headers)


# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")

# Environment Variable Configuration
def get_env_var(name: str, default: str = None):
    value = os.getenv(name, default)
    if value is None:
        logger.warning(f"Environment variable '{name}' not set.")
    return value

# Example API Router (Illustrative)
# @app.get("/nft-data/{nft_id}")
# async def get_nft_data(nft_id: str):
#     # Implement logic to fetch NFT data from your database or external sources
#     return JSONResponse(content={"nft_id": nft_id, "data": "Some NFT data"})

# Rate Limiting (Optional - Requires a rate limiting library)
# from fastapi.rate_limiting import RateLimit
# rate_limit = RateLimit(key_func=lambda: get_env_var("RATE_LIMIT_KEY"),
#                       limit=10,
#                       redis_store=RedisStore())
# @app.get("/analytics", rate_limit=rate_limit)
# async def analytics(portfolio_data: PortfolioData):
#     # ... your analytics logic ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)