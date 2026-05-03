from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
import os
import sys
from .health import health_check
from .exceptions import CustomException
from .utils import rate_limit

app = FastAPI(
    title="Mossland DAO Argus",
    description="AI-powered vulnerability detection tool for the Mossland DAO",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/docs/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Environment variable configuration
env_vars = os.environ.get("APP_SETTINGS", "development")
logger.info(f"Environment variables: {env_vars}")


# Health check endpoint
@app.get("/health", status_code=200)
async def health_check_endpoint():
    return health_check()


# Example API route (replace with your actual API logic)
@app.get("/api/data")
@rate_limit(max_requests=5, period=60)
async def get_data(request: Request):
    try:
        data = {
            "message": "Hello from Argus!",
            "timestamp": request.headers.get("X-Timestamp", None)
        }
        return JSONResponse(content=data)
    except Exception as e:
        logger.exception(f"Error in /api/data: {e}")
        raise CustomException(message="Internal Server Error", status_code=500)


@app.get("/api/error")
async def error_example():
    raise CustomException(message="Simulated Error", status_code=400)


# Exception handlers
@app.exception_handler(CustomException)
async def handle_exception(request, e):
    logger.exception(f"Exception caught: {e}")
    return JSONResponse(
        status_code=e.status_code,
        content={"error": e.message},
    )


# Lifespan events (startup/shutdown)
@app.on_event("startup")
async def startup_event():
    logger.info("Argus application startup complete.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Argus application shutdown complete.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)