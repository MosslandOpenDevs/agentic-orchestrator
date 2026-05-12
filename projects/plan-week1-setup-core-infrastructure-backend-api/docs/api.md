```markdown
# Smart Contract Analysis API Documentation

## 1. Overview

This API provides functionalities for analyzing smart contracts, retrieving contract details, and creating vulnerability reports. It leverages AI and Mythos for smart contract analysis and offers a streamlined workflow for developers to assess and manage their contracts.

## 2. Authentication Details

All API endpoints require an API key in the `X-API-Key` header.  This key must be provided for every request.  You can obtain your API key by registering an account through our platform.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. POST /api/contracts/analyze

*   **Method:** POST
*   **Path:** `/api/contracts/analyze`
*   **Description:** Analyzes a smart contract's code using AI and Mythos. This endpoint takes the smart contract code as input and performs a comprehensive analysis, identifying potential vulnerabilities and providing insights.
*   **Request Parameters/Body:**

    *   `contract_code` (string, required): The smart contract code to analyze.  Supported languages include Solidity, Vyper, and Rust.
    *   `language` (string, optional, default: "solidity"): The programming language of the smart contract.
*   **Response Format:** JSON

    ```json
    {
      "status": "success",
      "analysis_id": "unique_analysis_id",
      "report": {
        "vulnerabilities": [
          {
            "name": "Reentrancy Vulnerability",
            "severity": "High",
            "description": "The contract is vulnerable to reentrancy attacks...",
            "location": "contract.address#line_number"
          },
          {
            "name": "Integer Overflow",
            "severity": "Medium",
            "description": "Potential integer overflow in the contract...",
            "location": "contract.address#line_number"
          }
        ],
        "summary": "Overall analysis summary..."
      }
    }
    ```
*   **Example Request:**

    ```
    POST /api/contracts/analyze
    Content-Type: application/json
    X-API-Key: YOUR_API_KEY
    Content-Length: 123

    {
      "contract_code": "pragma solidity ^0.8.0;\n\ncontract MyContract {\n  // ... contract code ...\n}",
      "language": "solidity"
    }
    ```
*   **Example Response:** (Success)

    ```json
    {
      "status": "success",
      "analysis_id": "a1b2c3d4e5f6",
      "report": {
        "vulnerabilities": [
          {
            "name": "Reentrancy Vulnerability",
            "severity": "High",
            "description": "The contract is vulnerable to reentrancy attacks...",
            "location": "contract.address#line_number"
          }
        ],
        "summary": "Overall analysis summary..."
      }
    }
    ```

### 4.2. GET /api/contracts/:contractId

*   **Method:** GET
*   **Path:** `/api/contracts/:contractId` (Replace `:contractId` with the actual contract ID)
*   **Description:** Retrieves details for a specific smart contract.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON

    ```json
    {
      "contract_id": "unique_contract_id",
      "contract_name": "MyContract",
      "contract_code": "pragma solidity ^0.8.0;\n\ncontract MyContract {\n  // ... contract code ...\n}",
      "compiler_version": "0.8.0",
      "creation_date": "2023-10-27T10:00:00Z"
    }
    ```
*   **Example Request:**

    ```
    GET /api/contracts/a1b2c3d4e5f6
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (Success)

    ```json
    {
      "contract_id": "a1b2c3d4e5f6",
      "contract_name": "MyContract",
      "contract_code": "pragma solidity ^0.8.0;\n\ncontract MyContract {\n  // ... contract code ...\n}",
      "compiler_version": "0.8.0",
      "creation_date": "2023-10-27T10:00:00Z"
    }
    ```

### 4.3. POST /api/reports/create

*   **Method:** POST
*   **Path:** `/api/reports/create`
*   **Description:** Creates a new vulnerability report. This endpoint allows users to manually create reports based on their analysis findings.
*   **Request Parameters/Body:**

    *   `contract_id` (string, required): The ID of the smart contract the report applies to.
    *   `vulnerability_name` (string, required): The name of the vulnerability.
    *   `severity` (string, required): The severity level of the vulnerability (e.g., "High", "Medium", "Low").
    *   `description` (string, required): A detailed description of the vulnerability.
    *   `location` (string, required): The location of the vulnerability within the contract code (e.g., "contract.address#line_number").
*   **Response Format:** JSON

    ```json
    {
      "report_id": "unique_report_id",
      "status": "success",
      "created_at": "2023-10-27T11:00:00Z"
    }
    ```
*   **Example Request:**

    ```
    POST /api/reports/create
    Content-Type: application/json
    X-API-Key: YOUR_API_KEY
    Content-Length: 150

    {
      "contract_id": "a1b2c3d4e5f6",
      "vulnerability_name": "Reentrancy Vulnerability",
      "severity": "High",
      "description": "The contract is vulnerable to reentrancy attacks...",
      "location": "contract.address#line_number"
    }
    ```
*   **Example Response:** (Success)

    ```json
    {
      "report_id": "f7g8h9i0j1k2",
      "status": "success",
      "created_at": "2023-10-27T11:00:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters   | Validate request body and parameters |
| 401      | Unauthorized - Missing or invalid API key | Provide a valid API key            |
| 404      | Not Found - Contract or report not found | Verify contract ID and report ID     |
| 500      | Internal Server Error                    | Contact support for assistance      |
| 429      | Too Many Requests - Rate Limit Exceeded | Retry after a delay                 |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60
*   **Burst Capacity:** 120
*   **Reset Interval:** 60 seconds

Exceeding the rate limits will result in a 429 Too Many Requests error.  Please refer to our [API Usage Guidelines](https://example.com/api-usage-guidelines) for more details.
```