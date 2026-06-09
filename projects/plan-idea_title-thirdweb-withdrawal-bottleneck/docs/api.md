```markdown
# NFT Withdrawal & Claude Analysis API Documentation

## 1. Overview

This API provides endpoints for retrieving real-time NFT withdrawal transaction data, analyzing smart contract data with Claude Opus, and monitoring the status of external data feeds. It's designed to integrate with a decentralized NFT platform and provide valuable insights into transaction activity and smart contract health.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain your API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.yourplatform.com`

(Replace `https://api.yourplatform.com` with your actual API base URL)

## 4. Endpoints

### 4.1. GET /api/withdrawal_data

*   **Method:** `GET`
*   **Path:** `/api/withdrawal_data`
*   **Description:** Retrieves real-time NFT withdrawal transaction data from the blockchain.  This endpoint pulls data from the blockchain and provides a summary of recent withdrawals, including NFT ID, amount withdrawn, and timestamp.
*   **Request Parameters/Body:**
    *   None
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": [
        {
          "nft_id": "0x...",
          "amount": "1.23",
          "timestamp": "1678886400",
          "transaction_hash": "0x...",
          "withdrawal_status": "completed"
        },
        {
          "nft_id": "0x...",
          "amount": "0.50",
          "timestamp": "1678885600",
          "transaction_hash": "0x...",
          "withdrawal_status": "pending"
        }
      ],
      "total_withdrawals": 2
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        GET /api/withdrawal_data HTTP/1.1
        X-API-Key: YOUR_API_KEY
        ```

    *   **Response (Success):**
        ```json
        {
          "status": "success",
          "data": [ ... ],
          "total_withdrawals": 2
        }
        ```

*   **Error Codes:**
    *   `400 Bad Request`: Invalid API key.
    *   `500 Internal Server Error`:  Database or blockchain connection issues.

### 4.2. POST /api/claude_analysis

*   **Method:** `POST`
*   **Path:** `/api/claude_analysis`
*   **Description:** Sends smart contract data to the Claude Opus API for analysis. This endpoint allows you to submit smart contract data (e.g., transaction logs, state variables) to Claude Opus for automated analysis, such as anomaly detection or risk assessment.
*   **Request Parameters/Body:**
    *   `contract_address` (string, required): The address of the smart contract.
    *   `data` (string, required): The smart contract data to be analyzed.  This should be a JSON string representing the relevant data.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "analysis_result": "Claude Opus analysis complete.  Result: High Risk - Potential manipulation detected.",
      "claude_analysis_id": "ca-12345"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        POST /api/claude_analysis HTTP/1.1
        X-API-Key: YOUR_API_KEY
        Content-Type: application/json
        ```

        ```json
        {
          "contract_address": "0x...",
          "data": "{ \"timestamp\": \"1678886400\", \"value\": 100 }"
        }
        ```

    *   **Response (Success):**
        ```json
        {
          "status": "success",
          "analysis_result": "Claude Opus analysis complete. Result: Low Risk.",
          "claude_analysis_id": "ca-67890"
        }
        ```

*   **Error Codes:**
    *   `400 Bad Request`: Missing required parameters, invalid data format.
    *   `500 Internal Server Error`: Claude Opus API error.

### 4.3. GET /api/data_feed_status

*   **Method:** `GET`
*   **Path:** `/api/data_feed_status`
*   **Description:** Checks the status of external data feeds (Chainlink/API3).  This endpoint provides information about the connectivity and health of the data feeds used by the platform.
*   **Request Parameters/Body:**
    *   None
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "chainlink_status": "online",
      "api3_status": "online",
      "last_updated": "1678886400"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        GET /api/data_feed_status HTTP/1.1
        X-API-Key: YOUR_API_KEY
        ```

    *   **Response (Success):**
        ```json
        {
          "status": "success",
          "chainlink_status": "online",
          "api3_status": "online",
          "last_updated": "1678886400"
        }
        ```

*   **Error Codes:**
    *   `400 Bad Request`: Invalid API key.
    *   `500 Internal Server Error`:  Issues connecting to data feed services.

## 5. Error Codes and Handling

| Code    | Description               | Handling                               |
| :------ | :------------------------ | :------------------------------------- |
| 400      | Bad Request               | Validate request parameters.           |
| 401      | Unauthorized              | Verify API key.                        |
| 404      | Not Found                 | Check endpoint and resource existence. |
| 500      | Internal Server Error     | Log error, retry, or escalate.        |
| 503      | Service Unavailable       | Service is temporarily unavailable.     |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per minute:** 60 requests
*   **Burst Limit:** 120 requests (allowing for short bursts)
*   **Rate Limit Header:**  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response to indicate the current rate limit status.  For example:

    ```
    X-RateLimit-Limit: 60
    X-RateLimit-Remaining: 54
    X-RateLimit-Reset: 1678890000
    ```

    (These values will change dynamically based on usage.)
```
