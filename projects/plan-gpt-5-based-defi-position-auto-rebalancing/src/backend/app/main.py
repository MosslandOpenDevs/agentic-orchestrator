from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from datetime import datetime

app = FastAPI(
    title="Mossland DTCC/Chainlink Integration",
    description="A FastAPI application for integrating with DTCC and Chainlink.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for security
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
env_vars = {
    "DATABASE_URL": os.environ.get("DATABASE_URL", "postgresql://user:password@host:port/database"),
    "CHAINLINK_API_KEY": os.environ.get("CHAINLINK_API_KEY", "YOUR_CHAINLINK_API_KEY"),
    "CHAINLINK_NODE_ID": os.environ.get("CHAINLINK_NODE_ID", "YOUR_CHAINLINK_NODE_ID"),
    "JWT_SECRET": os.environ.get("JWT_SECRET", "YOUR_JWT_SECRET"),
}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Example API route (replace with actual implementation)
@app.get("/estimate-cost")
def estimate_cost():
    try:
        labor_cost = float(os.environ.get("LABOR_COST", 350000))
        infrastructure_cost = float(os.environ.get("INFRA_COST", 15000))
        software_cost = float(os.environ.get("SOFTWARE_COST", 7500))
        contingency_cost = float(os.environ.get("CONTINGENCY_COST", 45000))
        total_cost = labor_cost + infrastructure_cost + software_cost + contingency_cost
        return {"total_cost": total_cost}
    except ValueError as e:
        logger.error(f"Error calculating cost: {e}")
        raise HTTPException(status_code=500, detail="Error calculating cost")

# Example Exception Handler
@app.exception_handler(HTTPException)
def http_exception_handler(exception):
    if exception.status_code == 404:
        return {"message": "Resource not found"}
    else:
        logger.exception(exception)
        return {"message": "Internal Server Error", "detail": str(exception)}

# Lifespan events (startup/shutdown)
@app.on_event("startup")
def startup_event():
    logger.info("Application startup complete.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutdown complete.")

# Example Dependency (for demonstration purposes)
def get_env_var(key: str):
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value