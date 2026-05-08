from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging
import os
import uvicorn
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import JSON
from datetime import datetime

load_dotenv()

app = FastAPI(
    title="Mossland Agent",
    description="Agent-based development implementation",
    version="1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*"),
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

# Database setup
engine = create_engine(os.getenv("DATABASE_URL"))
Base = declarative_base()

# Define a simple model for NFT metadata
class NFTMetadata(Base):
    __tablename__ = "nft_metadata"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    blockchain = Column(String)
    risk_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    json_data = Column(JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "blockchain": self.blockchain,
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat(),
            "json_data": self.json_data,
        }


# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Example API endpoint (replace with actual logic)
@app.get("/nft_data")
async def get_nft_data(limit: int = 10):
    try:
        nft_data = session.query(NFTMetadata).limit(limit).all()
        return JSONResponse(content=nft_data, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching NFT data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NFT data")


# Example exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.exception(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Internal Server Error"},
    )


# Lifespan events (startup/shutdown)
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
    session.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)