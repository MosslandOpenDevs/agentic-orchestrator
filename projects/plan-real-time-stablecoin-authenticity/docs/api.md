```markdown
# StableCoin Risk & Transaction Analysis API Documentation

## 1. Overview

This API provides two key functionalities: assessing the risk associated with stablecoin holdings and analyzing transactions for potential fraudulent activity. It leverages an AI engine for transaction analysis and provides risk scores based on various factors.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain an API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.stablecoin.example.com`

## 4. Endpoints

### 4.1. GET /api/stablecoin/risk

**Method:** `GET`
**Path:** `/api/stablecoin/risk`
**Description:** Retrieves the risk score for a given stablecoin.

**Request Parameters:**

*   `stablecoin_id` (required, string): The unique identifier of the stablecoin.  This can be the ticker symbol (e.g., USDT, USDC) or a custom ID assigned by the system.

**Response Format:**

JSON

```json
{
  "stablecoin_id": "USDT",
  "risk_score": 65,
  "risk_level": "Medium",
  "description": "Moderate risk due to recent market volatility and trading volume.",
  "timestamp": "2023-10-27T10:00:00Z"
}
```

**Example Requests/Responses:**

**Request:**

```
GET /api/stablecoin/risk?stablecoin_id=USDT
```

**Response:**

```json
{
  "stablecoin_id": "USDT",
  "risk_score": 65,
  "risk_level": "Medium",
  "description": "Moderate risk due to recent market volatility and trading volume.",
  "timestamp": "2023-10-27T10:00:00Z"
}
```

### 4.2. POST /api/transaction/analyze

**Method:** `POST`
**Path:** `/api/transaction/analyze`
**Description:** Analyzes a transaction for potential fraud using the AI engine.

**Request Parameters:**

*   `transaction_id` (required, string): The unique identifier of the transaction.
*   `amount` (required, number): The transaction amount in the base currency (e.g., USD).
*   `sender_address` (required, string): The sender's address.
*   `receiver_address` (required, string): The receiver's address.
*   `timestamp` (optional, string, ISO 8601 format): The timestamp of the transaction. Defaults to the current time.

**Request Body (JSON):**

```json
{
  "transaction_id": "TX12345",
  "amount": 100.00,
  "sender_address": "0xAbCdEfGhIjKlmNopQrStUvW",
  "receiver_address": "0x1234567890abcdef1234567890abcdef",
  "timestamp": "2023-10-27T09:30:00Z"
}
```

**Response Format:**

JSON

```json
{
  "transaction_id": "TX12345",
  "analysis_result": "Fraudulent",
  "risk_score": 92,
  "confidence_level": 0.85,
  "reasoning": "High transaction amount combined with recent address activity suggests potential fraud.",
  "timestamp": "2023-10-27T09:35:00Z"
}
```

**Example Requests/Responses:**

**Request:**

```
POST /api/transaction/analyze
Content-Type: application/json

{
  "transaction_id": "TX12345",
  "amount": 100.00,
  "sender_address": "0xAbCdEfGhIjKlmNopQrStUvW",
  "receiver_address": "0x1234567890abcdef1234567890abcdef"
}
```

**Response:**

```json
{
  "transaction_id": "TX12345",
  "analysis_result": "Fraudulent",
  "risk_score": 92,
  "confidence_level": 0.85,
  "reasoning": "High transaction amount combined with recent address activity suggests potential fraud.",
  "timestamp": "2023-10-27T09:35:00Z"
}
```

## 5. Error Codes and Handling

| Code      | Description                               | Possible Cause                               |
|-----------|-------------------------------------------|---------------------------------------------|
| 400        | Bad Request                               | Invalid input data (e.g., missing parameters, incorrect data types) |
| 401        | Unauthorized                              | Missing or invalid API key                    |
| 404        | Not Found                                | Stablecoin ID or Transaction ID does not exist |
| 429        | Too Many Requests                        | Rate limit exceeded                          |
| 500        | Internal Server Error                    | Server-side error                              |

**Error Response Format:**

```json
{
  "error_code": 400,
  "message": "Invalid input data.  'stablecoin_id' is required."
}
```

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse.

*   **Requests per minute:** 60 requests
*   **Burst Limit:**  A burst of 120 requests is allowed, after which the rate limit resets.
*   **Rate Limit Header:**  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response to indicate the current rate limit status.  For example:

    `X-RateLimit-Limit: 60`
    `X-RateLimit-Remaining: 54`
    `X-RateLimit-Reset: 1678886400` (Unix timestamp)
```