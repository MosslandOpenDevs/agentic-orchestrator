```markdown
# Smart Contract API Documentation

## 1. Overview

This API provides endpoints for retrieving smart contract information, initiating LLM-based analysis, and generating remediated smart contracts. It's designed to assist developers in understanding and improving the security and functionality of their smart contracts.

## 2. Authentication Details

This API utilizes API key authentication.  You must include an `X-API-Key` header in all requests.  Contact your administrator to obtain an API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/contracts

*   **Method:** `GET`
*   **Path:** `/api/contracts`
*   **Description:** Retrieves a list of smart contracts.  Supports pagination and filtering.
*   **Request Parameters/Body:**
    *   `page` (optional, integer): The page number to retrieve (default: 1).
    *   `limit` (optional, integer): The number of contracts per page (default: 10, max: 100).
    *   `contractAddress` (optional, string): Filter by contract address.
    *   `contractName` (optional, string): Filter by contract name.
*   **Response Format:** JSON
    ```json
    {
      "page": 1,
      "limit": 10,
      "total": 123,
      "contracts": [
        {
          "contractAddress": "0x123...",
          "contractName": "MyContract",
          "deployedAt": "2023-10-26T10:00:00Z",
          "codeHash": "0x...",
          "balance": 1000.00
        },
        {
          "contractAddress": "0x456...",
          "contractName": "AnotherContract",
          "deployedAt": "2023-10-27T12:30:00Z",
          "codeHash": "0x...",
          "balance": 500.00
        }
      ]
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/contracts?page=2&limit=20`
    *   **Response:** (See JSON example above)

### 4.2. GET /api/contracts/{contractAddress}

*   **Method:** `GET`
*   **Path:** `/api/contracts/{contractAddress}`
*   **Description:** Retrieves details for a specific smart contract.
*   **Request Parameters/Body:**
    *   `contractAddress` (required, string): The address of the smart contract.
*   **Response Format:** JSON
    ```json
    {
      "contractAddress": "0x123...",
      "contractName": "MyContract",
      "deployedAt": "2023-10-26T10:00:00Z",
      "codeHash": "0x...",
      "balance": 1000.00,
      "creationDate": "2023-10-26T10:00:00Z",
      "owner": "0x...",
      "transactionCount": 5
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/contracts/0x123...`
    *   **Response:** (See JSON example above)

### 4.3. POST /api/analyze

*   **Method:** `POST`
*   **Path:** `/api/analyze`
*   **Description:** Initiates an LLM analysis of a smart contract.  Requires the smart contract source code.
*   **Request Parameters/Body:**
    *   `contractCode` (required, string): The source code of the smart contract.
    *   `analysisType` (optional, string): Type of analysis to perform (e.g., "security", "gas optimization"). Defaults to "security".
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "analysisId": "a1b2c3d4e5f6",
      "report": {
        "vulnerabilities": [
          {
            "type": "Reentrancy",
            "description": "The contract is vulnerable to reentrancy attacks...",
            "severity": "High",
            "line": 25
          }
        ],
        "gasOptimizationSuggestions": [
          {
            "description": "Optimize this loop...",
            "line": 10
          }
        ]
      }
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `POST /api/analyze` with JSON body:
        ```json
        {
          "contractCode": "contract MyContract { ... }",
          "analysisType": "gas optimization"
        }
        ```
    *   **Response:** (See JSON example above)

### 4.4. POST /api/remediate

*   **Method:** `POST`
*   **Path:** `/api/remediate`
*   **Description:** Generates a smart contract to remediate vulnerabilities. Requires the smart contract source code and analysis report ID.
*   **Request Parameters/Body:**
    *   `contractCode` (required, string): The source code of the smart contract.
    *   `analysisReportId` (required, string): The ID of the analysis report.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "remediatedContractCode": "contract MyContract Remediated { ... }",
      "changes": [
        "Fixed reentrancy vulnerability...",
        "Optimized gas usage..."
      ]
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `POST /api/remediate` with JSON body:
        ```json
        {
          "contractCode": "contract MyContract { ... }",
          "analysisReportId": "a1b2c3d4e5f6"
        }
        ```
    *   **Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input data         | Validate input and return detailed error message |
| 401      | Unauthorized - Invalid API key          | Provide correct API key             |
| 404      | Not Found - Resource not found           | Check resource URL and data           |
| 422      | Unprocessable Entity - Validation error | Check request body for errors        |
| 500      | Internal Server Error                    | Contact API administrator            |
| 503      | Service Unavailable - Temporarily down | Retry request later                 |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.

*   **Requests per minute:** 60
*   **Burst limit:** 120
*   **Reset interval:** 60 seconds

Exceeding the rate limits will result in a 429 (Too Many Requests) error.  Implement retry logic with exponential backoff.  See the `/health` endpoint for current rate limit status.
```
