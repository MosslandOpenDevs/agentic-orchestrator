```markdown
# Risk Assessment & Market Data API Documentation

## 1. Overview

This API provides endpoints for retrieving risk scores, real-time market data, and managing Claude Agent Prompts. It's designed to be used by developers building applications that require risk analysis and market insights related to cryptocurrency assets.

## 2. Authentication Details

Currently, this API does not require authentication for read-only operations (GET requests).  Future versions may require API keys for enhanced security and usage tracking.

## 3. Base URL Configuration

The base URL for all API requests is:

```
https://api.example.com/v1
```

(Replace `https://api.example.com/v1` with the actual base URL of your API)

## 4. Endpoints

### 4.1. GET /api/riskScore

*   **Method:** GET
*   **Path:** `/api/riskScore`
*   **Description:** Retrieves the risk score for a given wallet address. The risk score is calculated based on various on-chain metrics.
*   **Request Parameters/Body:**

    *   `walletAddress` (string, required): The Ethereum wallet address for which to retrieve the risk score.  Must be a valid Ethereum address.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/riskScore?walletAddress=0xd8dA6611e3B1a6Al82Lr67fKqEq7IDyXw54M2e3a
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "walletAddress": "0xd8dA6611e3B1a6Al82Lr67fKqEq7IDyXw54M2e3a",
      "riskScore": 72,
      "scoreDescription": "Moderate Risk - Potential for significant price fluctuations.",
      "timestamp": 1678886400
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Invalid wallet address format."
    }
    ```

### 4.2. GET /api/marketData

*   **Method:** GET
*   **Path:** `/api/marketData`
*   **Description:** Retrieves real-time market data for a given asset address.
*   **Request Parameters/Body:**

    *   `assetAddress` (string, required): The Ethereum asset address (e.g., ERC-20 token contract address) for which to retrieve market data.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/marketData?assetAddress=0x6B175474E89094C44Da98b954EedeDC73c077370
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "assetAddress": "0x6B175474E89094C44Da98b954EedeDC73c077370",
      "symbol": "ETH",
      "price": 3800.50,
      "volume24h": 1234567890.12,
      "marketCap": 420000000000,
      "timestamp": 1678886400
    }
    ```
*   **Example Response (Error - 404 Not Found):**

    ```json
    {
      "error": "Asset address not found."
    }
    ```

### 4.3. POST /api/agentPrompt

*   **Method:** POST
*   **Path:** `/api/agentPrompt`
*   **Description:** Stores a new Claude Agent Prompt.  This endpoint is used to manage and track prompts used by the Claude Agent system.
*   **Request Parameters/Body:**

    *   `prompt` (string, required): The Claude Agent prompt to store.
    *   `description` (string, optional): A description of the prompt.
    *   `createdBy` (string, optional): The user or system that created the prompt.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/agentPrompt
    Content-Type: application/json

    {
      "prompt": "Analyze recent price movements of Bitcoin and provide a short summary.",
      "description": "Prompt for Bitcoin analysis",
      "createdBy": "system"
    }
    ```
*   **Example Response (Success - 201 Created):**

    ```json
    {
      "id": "a1b2c3d4e5f6",
      "prompt": "Analyze recent price movements of Bitcoin and provide a short summary.",
      "description": "Prompt for Bitcoin analysis",
      "createdBy": "system",
      "createdAt": 1678886400
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Prompt cannot be empty."
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Possible Cause                               |
| :------ | :--------------------------------------- | :------------------------------------------ |
| 400      | Bad Request                              | Invalid input data, missing required fields |
| 404      | Not Found                               | Asset address or wallet address not found   |
| 429      | Too Many Requests                        | Rate limit exceeded                         |
| 500      | Internal Server Error                    | Server-side error                            |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests per minute per IP address.
*   **Burst Limit:** A short burst of up to 3 requests per minute is allowed.
*   **Reset:** Rate limits reset every 60 seconds.

If you exceed the rate limits, you will receive a 429 Too Many Requests error.  Implement retry logic with exponential backoff to handle these errors gracefully.
```
