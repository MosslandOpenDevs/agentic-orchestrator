from pydantic import BaseModel, Field
from typing import Optional

class FieldValidator:
    def __init__(self, validator_func):
        self.validator_func = validator_func

class SmartContract(BaseModel):
    contract_address: str = Field(..., description="The address of the smart contract on the Mossland chain", min_length=40, max_length=64)
    contract_name: str = Field(..., description="The name of the smart contract")
    contract_code_hash: str = Field(..., description="The hash of the smart contract code")
    deployed_at: str = Field(..., description="Timestamp of when the contract was deployed", format="%Y-%m-%dT%H:%M:%SZ")
    version: int = Field(2, description="The version of the smart contract", ge=2)
    schema_url: Optional[str] = Field(None, description="URL to the smart contract schema")
    config = {
        "yaml_alias": {
            None: "Optional[str]"
        }
    }

    class Create(SmartContract):
        pass

    class Update(SmartContract):
        pass

    class Response(SmartContract):
        class Meta:
            exclude = {"schema_url"}

class VulnerabilityReport(BaseModel):
    report_id: int = Field(..., description="Unique identifier for the vulnerability report", gt=0)
    contract_address: str = Field(..., description="The address of the smart contract affected by the vulnerability", min_length=40, max_length=64)
    vulnerability_type: str = Field(..., description="Type of vulnerability (e.g., Reentrancy, Overflow)", min_length=1, max_length=255)
    severity: str = Field("Medium", description="Severity level of the vulnerability (High, Medium, Low, Critical)", validate_enum=True)
    description: str = Field(..., description="Detailed description of the vulnerability")
    reporter: str = Field(..., description="Name of the reporter")
    timestamp: str = Field(..., description="Timestamp when the vulnerability was reported", format="%Y-%m-%dT%H:%M:%SZ")
    status: str = Field("Open", description="Status of the vulnerability report (Open, In Progress, Resolved, Closed)", validate_enum=True)
    evidence: Optional[str] = Field(None, description="Evidence supporting the vulnerability report")
    cvss_score: Optional[float] = Field(None, description="CVSS score of the vulnerability")
    config = {
        "yaml_alias": {
            None: "Optional[str]"
        }
    }

    class Create(VulnerabilityReport):
        pass

    class Update(VulnerabilityReport):
        pass

    class Response(VulnerabilityReport):
        class Meta:
            exclude = {"evidence", "cvss_score"}

class User(BaseModel):
    user_id: int = Field(..., description="Unique identifier for the user", gt=0)
    username: str = Field(..., description="User's username", min_length=3, max_length=32)
    email: str = Field(..., description="User's email address", email=True)
    password: str = Field(..., description="User's password", min_length=8)
    registration_date: str = Field(..., description="Timestamp of when the user registered", format="%Y-%m-%dT%H:%M:%SZ")
    role: str = Field("User", description="User's role (Admin, User, Auditor)", validate_enum=True)
    config = {
        "yaml_alias": {
            None: "Optional[str]"
        }
    }

    class Create(User):
        pass

    class Update(User):
        pass

    class Response(User):
        class Meta:
            exclude = {"registration_date"}