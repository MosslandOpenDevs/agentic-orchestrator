from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from .routes import router
from .health import health_check
from .config import Settings

app = FastAPI(
    title="Wagyu Rug Pull Detection System",
    description="A system for detecting and preventing rug pulls on decentralized exchanges.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load Configuration from Environment Variables
settings = Settings()
app.state.settings = settings

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.exception(exc)
    return HTTPException(
        status_code=exc.status_code,
        detail=str(exc),
    )

# Lifespan Events
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")
    # Initialize any necessary services here, e.g., database connections

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
    # Perform cleanup tasks here, e.g., closing database connections

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# API Router
app.include_router(router)

# Example Environment Variable Configuration (for demonstration)
@app.get("/config")
async def get_config():
    return settings.dict()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)