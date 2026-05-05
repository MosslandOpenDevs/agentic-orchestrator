from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
import logging
import os
from dotenv import load_dotenv
import uuid
import time
import json
from datetime import datetime

load_dotenv()

app = FastAPI(
    title="DTCC Tokenized Security Platform",
    description="A platform for managing tokenized securities with DTCC integration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "*")],
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


# Dependency for handling errors
def handle_exception(e: HTTPException):
    logger.exception("An error occurred")
    raise e


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Dummy data for demonstration
@app.get("/data")
def get_data():
    return {
        "dtcc_security_price": 123.45,
        "crypto_price": 678.90,
        "timestamp": datetime.now().isoformat()
    }


# Dummy endpoint for testing
@app.get("/dummy")
def dummy_endpoint():
    return {"message": "This is a dummy endpoint"}


# Example of a rate limiting decorator (optional)
# from fastapi.responses import HTTPExceptionResponse
# from fastapi import FastAPI, Request
#
# @app.on_event("startup")
# async def startup_event():
#     # Configure rate limiting here (e.g., using a library like Flask-Limiter)
#     pass
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     # Cleanup resources here
#     pass

# Example of a simple route with error handling
@app.get("/example")
async def example_route():
    try:
        # Simulate an error
        # raise ValueError("Simulated error")
        return {"message": "Example route successful"}
    except Exception as e:
        logger.exception("Error in example route")
        raise handle_exception(HTTPException(status_code=500, detail=str(e)))

# Example of a route with dependency injection
# @app.get("/data-with-dependency")
# async def data_with_dependency():
#     # Simulate fetching data
#     data = {"data": "Some data"}
#     return data


# Example of a route with environment variable access
@app.get("/env-var")
def get_env_var():
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not found")
    return {"api_key": api_key}


# Example of a route with UUID generation
@app.post("/generate-uuid")
def generate_uuid():
    uuid_value = str(uuid.uuid4())
    return {"uuid": uuid_value}


# Example of a route with WebSocket integration (placeholder)
@app.get("/websocket")
async def websocket_route():
    return {"message": "Connected to WebSocket"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)