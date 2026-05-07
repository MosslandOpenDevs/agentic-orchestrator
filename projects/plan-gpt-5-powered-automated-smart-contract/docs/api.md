```markdown
# Smart Contract Analysis API Documentation

## 1. Overview

This API provides tools for analyzing smart contracts, generating vulnerability reports, and assessing dynamic risk. It leverages GPT-5 for vulnerability analysis and offers a risk assessment service based on contract activity. This documentation outlines the available endpoints, their parameters, response formats, and error handling.

## 2. Authentication Details

This API requires an API key for authentication.  You can obtain an API key by registering an account through our platform.  The API key must be included in the `X-API-Key` header for all requests.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/contracts

*   **Method:** `GET`
*   **Path:** `/api/contracts`
*   **Description:** Retrieves a list of all smart contracts.
*   **Request Parameters/Body:**
    *   `limit`: (Optional, Integer) - Limits the number of contracts returned. Default: 10. Max: 100.
    *   `offset`: (Optional, Integer) - Specifies the starting index of the results. Default: 0.
*   **Response Format:** JSON Array
    ```json
    [
      {
        "contractAddress": "0x...",
        "contractName": "MyContract",
        "creationDate": "2023-10-26T10:00:00Z",
        "codeHash": "...",
        "deployedCount": 12
      },
      {
        "contractAddress": "0x...",
        "contractName": "AnotherContract",
        "creationDate": "2023-10-27T14:30:00Z",
        "codeHash": "...",
        "deployedCount": 5
      }
    ]
    ```
*   **Example Request:**

    ```
    GET /api/contracts?limit=20&offset=0
    ```
*   **Example Response:** (See JSON response format above)

### 4.2. GET /api/contracts/{contractAddress}

*   **Method:** `GET`
*   **Path:** `/api/contracts/{contractAddress}`
*   **Description:** Retrieves details for a specific smart contract.
*   **Request Parameters/Body:**
    *   `contractAddress`: (Required, String) - The address of the smart contract.
*   **Response Format:** JSON
    ```json
    {
      "contractAddress": "0x...",
      "contractName": "MyContract",
      "creationDate": "2023-10-26T10:00:00Z",
      "codeHash": "...",
      "deployedCount": 12,
      "contractSize": 1500,
      "deployedBlocks": 100
    }
    ```
*   **Example Request:**

    ```
    GET /api/contracts/0x1234567890abcdef1234567890abcdef12345678
    ```
*   **Example Response:** (See JSON response format above)

### 4.3. POST /api/vulnerabilities

*   **Method:** `POST`
*   **Path:** `/api/vulnerabilities`
*   **Description:** Generates a vulnerability report for a smart contract using GPT-5.
*   **Request Parameters/Body:**
    *   `contractAddress`: (Required, String) - The address of the smart contract.
    *   `prompt`: (Optional, String) -  A custom prompt to guide GPT-5. If not provided, a default prompt will be used.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "reportId": "...",
      "vulnerabilityReport": "GPT-5 generated vulnerability report..."
    }
    ```
*   **Example Request:**

    ```
    POST /api/vulnerabilities
    Content-Type: application/json

    {
      "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "prompt": "Analyze this contract for common vulnerabilities like reentrancy and integer overflows."
    }
    ```
*   **Example Response:** (See JSON response format above)

### 4.4. GET /api/risk/{contractAddress}

*   **Method:** `GET`
*   **Path:** `/api/risk/{contractAddress}`
*   **Description:** Retrieves the dynamic risk assessment for a smart contract.
*   **Request Parameters/Body:**
    *   `contractAddress`: (Required, String) - The address of the smart contract.
*   **Response Format:** JSON
    ```json
    {
      "contractAddress": "0x...",
      "riskScore": 0.75,
      "riskCategory": "Medium",
      "lastUpdated": "2023-11-15T12:00:00Z",
      "activitySummary": {
        "transactions": 50,
        "uniqueAddresses": 10
      }
    }
    ```
*   **Example Request:**

    ```
    GET /api/risk/0x1234567890abcdef1234567890abcdef12345678
    ```
*   **Example Response:** (See JSON response format above)

## 5. Error Codes and Handling

| Code      | Description                               | Action                               |
|-----------|-------------------------------------------|-------------------------------------|
| 400        | Bad Request - Invalid input parameters     | Check request body and parameters    |
| 401        | Unauthorized - Missing or invalid API key | Provide a valid API key in the header |
| 404        | Not Found - Contract not found             | Verify contract address             |
| 429        | Too Many Requests - Rate Limit Exceeded  | Retry after a delay                 |
| 500        | Internal Server Error                     | Contact support for assistance       |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for short bursts exceeding the rate limit)
*   **Reset Time:** 60 seconds

Rate limiting is enforced on a per-API key basis.  Exceeding the rate limits will result in a 429 Too Many Requests error.  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be returned with each request to provide real-time rate limit information.
```