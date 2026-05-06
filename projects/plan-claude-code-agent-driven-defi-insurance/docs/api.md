```markdown
# NFT Portfolio Management API Documentation

## 1. Overview

This API provides functionalities for managing NFT portfolios, including retrieving portfolio data, initiating rebalancing, and performing risk assessments. It is designed to be used by developers building applications that interact with NFT holdings and require automated portfolio management and risk analysis.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain a valid API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/portfolio/{nftHolderId}

*   **Method:** GET
*   **Path:** `/api/portfolio/{nftHolderId}`
*   **Description:** Retrieves the portfolio data for a given NFT holder. This includes the NFTs held by the holder and their current values.
*   **Request Parameters:**
    *   `nftHolderId` (Path Parameter):  A unique identifier for the NFT holder.  Must be a valid integer.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/portfolio/123
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:**

    ```json
    {
      "nftHolderId": 123,
      "portfolio": [
        {
          "contractAddress": "0x...",
          "tokenId": "...",
          "name": "...",
          "tokenQuantity": 3,
          "currentValue": 150.00
        },
        {
          "contractAddress": "0x...",
          "tokenId": "...",
          "name": "...",
          "tokenQuantity": 1,
          "currentValue": 200.00
        }
      ]
    }
    ```

### 4.2. POST /api/rebalance/{nftHolderId}

*   **Method:** POST
*   **Path:** `/api/rebalance/{nftHolderId}`
*   **Description:** Initiates portfolio rebalancing based on AI agent's recommendations. This endpoint triggers a rebalancing process, moving funds between NFTs to align with the AI agent’s suggested portfolio allocation.
*   **Request Parameters:**
    *   `nftHolderId` (Path Parameter): A unique identifier for the NFT holder.  Must be a valid integer.
    *   `strategy` (Optional Query Parameter):  Specifies the rebalancing strategy to use.  Defaults to 'optimal'.  Possible values: 'optimal', 'conservative', 'aggressive'.
*   **Request Body:** (JSON)
    ```json
    {
      "rebalance": true
    }
    ```
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/rebalance/123?strategy=conservative
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "rebalance": true
    }
    ```
*   **Example Response (Success):**

    ```json
    {
      "status": "success",
      "message": "Portfolio rebalancing initiated successfully.",
      "rebalancingId": "unique_rebalancing_id"
    }
    ```

*   **Example Response (Error - Insufficient Funds):**

    ```json
    {
      "status": "error",
      "message": "Insufficient funds to execute rebalancing strategy."
    }
    ```

### 4.3. GET /api/riskAssessment/{contractAddress}

*   **Method:** GET
*   **Path:** `/api/riskAssessment/{contractAddress}`
*   **Description:** Retrieves the risk assessment for a given smart contract. This endpoint analyzes the smart contract's data and provides a risk score and associated risk factors.
*   **Request Parameters:**
    *   `contractAddress` (Path Parameter): The address of the smart contract to assess. Must be a valid Ethereum address.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/riskAssessment/0x...
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:**

    ```json
    {
      "contractAddress": "0x...",
      "riskScore": 0.75,
      "riskFactors": {
        "liquidity": 0.6,
        "volatility": 0.8,
        "smartContractAudited": true
      },
      "assessmentTimestamp": "2023-10-27T10:00:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code      | Description                               | Possible Cause                               |
|-----------|-------------------------------------------|---------------------------------------------|
| 400        | Bad Request                               | Invalid input data, missing parameters        |
| 401        | Unauthorized                              | Invalid API key or insufficient permissions  |
| 404        | Not Found                                | Requested resource does not exist              |
| 429        | Too Many Requests                         | Rate limit exceeded                          |
| 500        | Internal Server Error                     | Server-side error                              |

**Error Response Format (Example):**

```json
{
  "code": 400,
  "message": "Invalid nftHolderId format."
}
```

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for short bursts of activity)
*   **Reset Time:** 60 seconds

Exceeding the rate limits will result in a `429 Too Many Requests` error.  Implement retry logic with exponential backoff to handle temporary rate limiting issues.  Detailed rate limiting information is available via the `/api/health` endpoint (not documented here for brevity).
```
