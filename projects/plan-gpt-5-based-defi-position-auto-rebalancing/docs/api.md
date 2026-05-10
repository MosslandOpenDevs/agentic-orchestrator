```markdown
# NFT Portfolio Management API Documentation

## 1. Overview

This API provides tools for managing and predicting the value of your NFT portfolio. It integrates real-time market data, GPT-5 predictions, and allows for automated portfolio rebalancing. This API is designed for developers building applications that interact with NFT portfolios.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  You can obtain an API key by registering an account on our platform.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with the actual base URL)

## 4. Endpoints

### 4.1. GET /api/nft/portfolio

*   **Method:** `GET`
*   **Path:** `/api/nft/portfolio`
*   **Description:** Retrieves a user's NFT portfolio holdings.
*   **Request Parameters/Body:**
    *   `user_id` (required): The ID of the user whose portfolio is being requested.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/portfolio?user_id=123
    ```
*   **Example Response:**

    ```json
    {
      "user_id": 123,
      "portfolio": [
        {
          "nft_id": "NFT-001",
          "name": "CryptoPunks #1234",
          "token_name": "Ethereum",
          "token_symbol": "ETH",
          "quantity": 2,
          "current_value": 25000.00,
          "last_updated": "2023-10-27T10:00:00Z"
        },
        {
          "nft_id": "NFT-002",
          "name": "Bored Ape Yacht Club #5678",
          "token_name": "Ethereum",
          "token_symbol": "ETH",
          "quantity": 1,
          "current_value": 180000.00,
          "last_updated": "2023-10-27T10:00:00Z"
        }
      ]
    }
    ```

### 4.2. POST /api/portfolio/rebalance

*   **Method:** `POST`
*   **Path:** `/api/portfolio/rebalance`
*   **Description:** Initiates portfolio rebalancing based on market data and predictions.
*   **Request Parameters/Body:**
    *   `user_id` (required): The ID of the user whose portfolio is being rebalanced.
    *   `rebalance_strategy` (optional):  The rebalancing strategy to use (e.g., "aggressive", "conservative", "market").  Defaults to "market".
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/portfolio/rebalance
    Content-Type: application/json

    {
      "user_id": 456,
      "rebalance_strategy": "aggressive"
    }
    ```
*   **Example Response:**

    ```json
    {
      "status": "success",
      "message": "Portfolio rebalancing initiated successfully.",
      "rebalancing_details": {
        "nft_id": "NFT-001",
        "new_quantity": 1,
        "old_quantity": 2
      }
    }
    ```

### 4.3. GET /api/nft/prediction

*   **Method:** `GET`
*   **Path:** `/api/nft/prediction`
*   **Description:** Retrieves a GPT-5 prediction for an NFT's value.
*   **Request Parameters/Body:**
    *   `nft_id` (required): The ID of the NFT for which to generate a prediction.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/prediction?nft_id=NFT-001
    ```
*   **Example Response:**

    ```json
    {
      "nft_id": "NFT-001",
      "predicted_value": 27500.00,
      "confidence_level": 0.85,
      "prediction_timestamp": "2023-10-27T11:00:00Z",
      "model_version": "GPT-5"
    }
    ```

### 4.4. GET /api/marketdata

*   **Method:** `GET`
*   **Path:** `/api/marketdata`
*   **Description:** Retrieves real-time market data for NFTs.
*   **Request Parameters/Body:**
    *   `nft_id` (optional): Filter by a specific NFT ID.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/marketdata?nft_id=NFT-001
    ```
*   **Example Response:**

    ```json
    {
      "nft_id": "NFT-001",
      "token_name": "Ethereum",
      "token_symbol": "ETH",
      "current_price": 1800.00,
      "24h_change": 2.50,
      "volume_24h": 123456789,
      "market_cap": 10000000000,
      "last_updated": "2023-10-27T10:30:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Response Format  |
| :------ | :--------------------------------------- | :--------------- |
| 400      | Bad Request - Invalid input parameters.   | JSON with error details |
| 401      | Unauthorized - Invalid API key.          | JSON with error details |
| 404      | Not Found - Resource not found.           | JSON with error details |
| 500      | Internal Server Error - Server error.    | JSON with error details |
| 503      | Service Unavailable - Service unavailable. | JSON with error details |

**Example Error Response (401):**

```json
{
  "error_code": 401,
  "message": "Invalid API key."
}
```

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for a short burst of activity)
*   **Reset Time:** 60 seconds

Rate limits are enforced on a per-user basis.  If you exceed the rate limits, you will receive a `429 Too Many Requests` error.  Consult the API documentation for details on handling rate limiting errors and potential rate limit increase requests.
```
