```markdown
# Smart Contract Analysis API Documentation

## 1. Overview

This API provides tools for analyzing smart contracts, retrieving vulnerability reports, and managing user accounts. It leverages AI and Mythos to provide comprehensive contract analysis and reporting capabilities. This documentation outlines the available endpoints, authentication requirements, and expected response formats.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be obtained through user registration or administrator provisioning.  The API key is case-sensitive.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual base URL)

## 4. Endpoints

### 4.1. POST /api/contracts/analyze

*   **Method:** POST
*   **Path:** `/api/contracts/analyze`
*   **Description:** Analyzes a smart contract's code using AI and Mythos.  This endpoint takes the contract source code as input and performs static analysis to identify potential vulnerabilities and security issues.
*   **Request Parameters/Body:**

    *   `contract_code` (string, required): The smart contract's source code.  Supported languages include Solidity, Vyper, and Rust.
    *   `language` (string, optional, default: "solidity"): The programming language of the contract code.
*   **Response Format:** JSON

    ```json
    {
      "status": "success",
      "analysis_id": "unique_analysis_id",
      "report": {
        "vulnerabilities": [
          {
            "id": "vulnerability_1",
            "severity": "high",
            "description": "Potential Reentrancy Vulnerability",
            "line": 123,
            "code": "contract.function_that_reentrances()"
          }
        ],
        "summary": "Analysis complete.  Review the vulnerabilities listed above."
      }
    }
    ```
*   **Example Request:**

    ```
    POST /api/contracts/analyze
    Content-Type: application/json
    X-API-Key: your_api_key
    ```

    ```json
    {
      "contract_code": "pragma solidity ^0.8.0;\n\ncontract MyContract {\n    address owner;\n\n    constructor() {\n        owner = msg.sender;\n    }}\n\n    function transfer(address _to, uint _value) public {\n        // Vulnerability example\n        // ...\n    }\n}",
      "language": "solidity"
    }
    ```
*   **Example Response:** (Successful)

    ```json
    {
      "status": "success",
      "analysis_id": "a1b2c3d4e5f6",
      "report": {
        "vulnerabilities": [
          {
            "id": "vulnerability_1",
            "severity": "high",
            "description": "Potential Reentrancy Vulnerability",
            "line": 123,
            "code": "contract.function_that_reentrances()"
          }
        ],
        "summary": "Analysis complete.  Review the vulnerabilities listed above."
      }
    }
    ```

### 4.2. GET /api/contracts/:contractId/reports

*   **Method:** GET
*   **Path:** `/api/contracts/:contractId/reports`
*   **Description:** Retrieves vulnerability reports for a specific smart contract.
*   **Request Parameters/Body:**

    *   `contractId` (string, required): The unique identifier of the smart contract.
*   **Response Format:** JSON

    ```json
    {
      "status": "success",
      "report": {
        "vulnerabilities": [
          {
            "id": "vulnerability_1",
            "severity": "critical",
            "description": "Integer Overflow Vulnerability",
            "line": 45,
            "code": "uint256(x) + 1;"
          }
        ],
        "total_vulnerabilities": 1,
        "last_analyzed_at": "2023-10-27T10:00:00Z"
      }
    }
    ```
*   **Example Request:**

    ```
    GET /api/contracts/0x1234567890abcdef01234567890abcdef/reports
    X-API-Key: your_api_key
    ```
*   **Example Response:** (Successful)

    ```json
    {
      "status": "success",
      "report": {
        "vulnerabilities": [
          {
            "id": "vulnerability_1",
            "severity": "critical",
            "description": "Integer Overflow Vulnerability",
            "line": 45,
            "code": "uint256(x) + 1;"
          }
        ],
        "total_vulnerabilities": 1,
        "last_analyzed_at": "2023-10-27T10:00:00Z"
      }
    }
    ```

### 4.3. POST /api/users/register

*   **Method:** POST
*   **Path:** `/api/users/register`
*   **Description:** Registers a new user.
*   **Request Parameters/Body:**

    *   `username` (string, required): The desired username.
    *   `email` (string, required): The user's email address.
    *   `password` (string, required): The user's password.
*   **Response Format:** JSON

    ```json
    {
      "status": "success",
      "message": "User registered successfully."
    }
    ```
*   **Example Request:**

    ```
    POST /api/users/register
    Content-Type: application/json
    X-API-Key: your_api_key
    ```

    ```json
    {
      "username": "newuser",
      "email": "newuser@example.com",
      "password": "securepassword"
    }
    ```
*   **Example Response:** (Successful)

    ```json
    {
      "status": "success",
      "message": "User registered successfully."
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.          |
| 401      | Unauthorized - Invalid API key.         |
| 404      | Not Found - Resource not found.         |
| 500      | Internal Server Error - Server error.    |
| 429      | Too Many Requests - Rate limit exceeded.|

**Error Response Format:**

```json
{
  "error_code": "400",
  "message": "Invalid input data provided."
}
```

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse.  The following rate limits apply:

*   100 requests per minute per API key.

If the rate limit is exceeded, a `429 Too Many Requests` error will be returned.  Implement retry logic with exponential backoff to handle rate limiting gracefully.
```