```markdown
# NFT Withdrawal & Claude Analysis API Documentation

## 1. Overview

This API provides endpoints for retrieving real-time NFT withdrawal transaction data and sending smart contract data to Claude Opus for advanced analysis.  It's designed to integrate with blockchain data sources and leverage AI for deeper insights.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain a valid API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/withdrawal_data

*   **Method:** `GET`
*   **Path:** `/api/withdrawal_data`
*   **Description:** Retrieves real-time NFT withdrawal transaction data from the blockchain. This endpoint fetches recent withdrawal transactions and returns them in a structured format.
*   **Request Parameters/Body:**
    *   `limit` (Optional, Integer):  The maximum number of withdrawal transactions to return. Defaults to 10.  Maximum value: 100.
    *   `offset` (Optional, Integer): The offset from which to start returning transactions. Defaults to 0.
    *   `blockchain` (Optional, String):  The blockchain network to query (e.g., 'ethereum', 'polygon', 'arbitrum').  Defaults to 'ethereum'.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": [
        {
          "transactionHash": "0x...",
          "nftContractAddress": "0x...",
          "nftTokenId": "0x...",
          "timestamp": "2023-10-27T10:00:00Z",
          "senderAddress": "0x...",
          "recipientAddress": "0x...",
          "amount": "1.23",
          "status": "completed"
        },
        {
          "transactionHash": "0x...",
          "nftContractAddress": "0x...",
          "nftTokenId": "0x...",
          "timestamp": "2023-10-27T09:30:00Z",
          "senderAddress": "0x...",
          "recipientAddress": "0x...",
          "amount": "0.56",
          "status": "pending"
        }
      ],
      "totalCount": 100 // Total number of withdrawals matching the criteria
    }
    ```
*   **Example Requests:**
    *   `GET /api/withdrawal_data?limit=20&offset=0`
    *   `GET /api/withdrawal_data?limit=50&blockchain=polygon`
*   **Example Responses:** (See JSON response format above)

### 4.2. POST /api/claude_analysis

*   **Method:** `POST`
*   **Path:** `/api/claude_analysis`
*   **Description:** Sends smart contract data to Claude Opus for analysis and receives the response. This endpoint utilizes Claude Opus to analyze the provided smart contract data and generate a response based on the analysis.
*   **Request Parameters/Body:**
    *   `contractData` (Required, String): The smart contract data to be analyzed.  This should be a JSON string representing the relevant data.  Example: `{"contractAddress": "0x...", "functionName": "transfer", "parameters": ["0x...", "0.5"]}`
    *   `analysisType` (Optional, String): The type of analysis to perform.  Valid values: 'summary', 'risk_assessment', 'transaction_analysis'. Defaults to 'summary'.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "response": "Claude's analysis of the contract data...",
      "timestamp": "2023-10-27T11:00:00Z"
    }
    ```
*   **Example Requests:**
    *   `POST /api/claude_analysis` with body: `{"contractAddress": "0x...", "functionName": "transfer", "parameters": ["0x...", "0.5"]}`
    *   `POST /api/claude_analysis?analysisType=risk_assessment` with body: `{"contractAddress": "0x...", "functionName": "transfer", "parameters": ["0x...", "0.5"]}`
*   **Example Responses:** (See JSON response format above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input data         | Validate request parameters and body  |
| 401      | Unauthorized - Invalid API key          | Provide a valid API key in the header |
| 404      | Not Found - Endpoint or resource not found | Verify endpoint and resource URL      |
| 500      | Internal Server Error - Server issue     | Contact support for assistance       |
| 503      | Service Unavailable - Temporary outage   | Retry request later                 |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure stability.

*   **Requests per minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for a short burst of activity)
*   **Reset Time:** 60 seconds (after exceeding the rate limit)

Rate limiting is enforced based on the API key.  If you exceed the rate limit, you will receive a `429 Too Many Requests` error.  The `Retry-After` header will indicate when the rate limit resets.  Example: `Retry-After: 60` (seconds).
```
