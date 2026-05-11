from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from typing import List
import openai
import etherscan
import json
from datetime import datetime

app = FastAPI(
    title="Quantum Vulnerability Scanner",
    description="A system for analyzing smart contract vulnerabilities using LLMs and risk scoring.",
    version="0.1.0",
)

# Configure CORS
origins = ["http://localhost:8000", "http://localhost:3000"]  # Add your frontend origin here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variable configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "YOUR_ETHERSCAN_API_KEY")

# Pydantic models
class ContractData(BaseModel):
    address: str
    contract_name: str
    code_hash: str
    transaction_count: int
    creation_date: str

class RiskScore(BaseModel):
    contract_address: str
    risk_score: float
    vulnerabilities: List[str]

# OpenAI API setup
openai.api_key = OPENAI_API_KEY

# Etherscan API setup
etherscan = etherscan.Etherscan(api_key=ETHERSCAN_API_KEY)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

# Dummy data collection (replace with Etherscan API integration)
def collect_data(address: str) -> List[ContractData]:
    # Simulate data retrieval from Etherscan
    # Replace with actual Etherscan API calls
    if address == "0x123":
        return [
            ContractData(address="0x123", contract_name="ContractA", code_hash="0x123", transaction_count=10, creation_date="2023-01-01"),
            ContractData(address="0x456", contract_name="ContractB", code_hash="0x456", transaction_count=5, creation_date="2023-02-15")
        ]
    else:
        return []

# Vulnerability analysis engine
def analyze_vulnerabilities(contract_data: ContractData) -> List[str]:
    prompt = f"""
    Analyze the following smart contract code for vulnerabilities:
    {contract_data.code_hash}
    Identify potential vulnerabilities such as reentrancy, integer overflows, and timestamp dependence.
    Return a list of vulnerabilities found.
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip().split(", ")

# Risk scoring system
def calculate_risk_score(contract_data: ContractData, vulnerabilities: List[str]) -> float:
    score = 0.0
    if "reentrancy" in vulnerabilities:
        score += 0.5
    if "integer overflow" in vulnerabilities:
        score += 0.3
    if "timestamp dependence" in vulnerabilities:
        score += 0.2
    return score

# Smart contract generation prototype
def generate_mitigation_code(vulnerabilities: List[str]) -> str:
    prompt = f"""
    Generate simple smart contract code to mitigate the following vulnerabilities:
    {', '.join(vulnerabilities)}
    Return the generated code.
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].text.strip()

# API endpoints
@app.get("/contracts/{address}", response_model=List[ContractData])
def get_contracts(address: str):
    data = collect_data(address)
    return data

@app.post("/analyze/{address}", response_model=RiskScore)
def analyze_contract(address: str):
    contract_data = collect_data(address)
    if not contract_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    vulnerabilities = analyze_vulnerabilities(contract_data[0])
    risk_score = calculate_risk_score(contract_data[0], vulnerabilities)
    mitigation_code = generate_mitigation_code(vulnerabilities)
    return RiskScore(
        contract_address=address,
        risk_score=risk_score,
        vulnerabilities=vulnerabilities
    )

@app.get("/health")
def health():
    return {"status": "ok"}