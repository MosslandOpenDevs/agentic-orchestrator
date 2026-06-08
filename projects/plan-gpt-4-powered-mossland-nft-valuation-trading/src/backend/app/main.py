from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(
    title="Mossland DeFi Portfolio Optimizer",
    description="Automated DeFi portfolio optimization for Mossland NFT holders using AI, mitigating yield-seeking risk.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS", "*")],
    allow_credentials=True,
    allow_headers=["Access-Control-Allow-Origin"],
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Example API route (replace with actual AI logic)
@app.get("/optimize")
def optimize_portfolio(cryptos: List[str]):
    try:
        # Simulate AI optimization
        optimized_portfolio = {
            "cryptos": cryptos,
            "strategy": "Conservative Yield"
        }
        return optimized_portfolio
    except Exception as e:
        logger.error(f"Error during optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize portfolio")


@app.on_event("startup")
def startup_event():
    logger.info("Application startup")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown")

# Example exception handler
@app.exception_handler(HTTPException)
def http_exception_handler(exception):
    if exception.status_code == 404:
        return {"message": "Resource not found"}
    return {"message": "Internal server error", "detail": str(exception)}