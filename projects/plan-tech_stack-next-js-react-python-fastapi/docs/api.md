```markdown
# Smart Contract Analysis API Documentation

## 1. Overview

This API provides endpoints for retrieving information about smart contracts and their associated transactions, as well as creating new vulnerability predictions. It's designed to assist in analyzing blockchain security and identifying potential vulnerabilities within smart contracts.

## 2. Authentication Details

Currently, this API does not require authentication. All endpoints are publicly accessible.  Future versions may require API keys or JWT authentication.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`

(Replace `https://api.example.com/v1` with the actual base URL of your API)

## 4. Endpoints

### 4.1. GET /api/contracts

*   **Method:** `GET`
*   **Path:** `/api/contracts`
*   **Description:** Retrieves a list of smart contracts.  Supports pagination and filtering.
*   **Request Parameters/Body:**
    *   `page`: (Optional, Integer) The page number to retrieve (default: 1).
    *   `limit`: (Optional, Integer) The number of contracts to return per page (default: 10, max: 100).
    *   `contract_name`: (Optional, String) Filter contracts by name.
    *   `contract_address`: (Optional, String) Filter contracts by address.
*   **Response Format:** JSON
    ```json
    {
      "data": [
        {
          "address": "0x...",
          "name": "Contract A",
          "deployed_at": "2023-10-26T10:00:00Z",
          "contract_type": "ERC20"
        },
        {
          "address": "0x...",
          "name": "Contract B",
          "deployed_at": "2023-10-27T12:30:00Z",
          "contract_type": "NFT"
        }
      ],
      "pagination": {
        "current_page": 1,
        "total_pages": 2,
        "total_contracts": 2,
        "limit": 10
      }
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/contracts?page=2&limit=20`
    *   **Response:** (See JSON response above)

### 4.2. GET /api/contracts/:address/transactions

*   **Method:** `GET`
*   **Path:** `/api/contracts/:address/transactions`
*   **Description:** Retrieves transactions for a specific smart contract address.
*   **Request Parameters/Body:**
    *   `:address`: (Required, String) The Ethereum address of the smart contract.
    *   `page`: (Optional, Integer) The page number to retrieve (default: 1).
    *   `limit`: (Optional, Integer) The number of transactions to return per page (default: 10, max: 100).
    *   `from_block`: (Optional, String) The block number to start retrieving transactions from (e.g., "latest", "0x...")
    *   `to_block`: (Optional, String) The block number to stop retrieving transactions (e.g., "latest", "0x...")
*   **Response Format:** JSON
    ```json
    {
      "data": [
        {
          "transaction_hash": "0x...",
          "block_number": "0x...",
          "timestamp": "2023-10-28T14:00:00Z",
          "from": "0x...",
          "to": "0x...",
          "value": "0x...",
          "input": "0x..."
        }
      ],
      "pagination": {
        "current_page": 1,
        "total_pages": 2,
        "total_transactions": 5,
        "limit": 10
      }
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/contracts/0x1234567890abcdef/transactions?page=1&limit=5`
    *   **Response:** (See JSON response above)

### 4.3. POST /api/predictions

*   **Method:** `POST`
*   **Path:** `/api/predictions`
*   **Description:** Creates a new vulnerability prediction.
*   **Request Parameters/Body:**
    *   `contract_address`: (Required, String) The Ethereum address of the smart contract.
    *   `prediction_text`: (Required, String) The text of the vulnerability prediction.
    *   `severity`: (Optional, String) The severity level of the prediction (e.g., "high", "medium", "low"). Defaults to "medium".
    *   `description`: (Optional, String) A detailed description of the prediction.
*   **Response Format:** JSON
    ```json
    {
      "id": "UUID",
      "contract_address": "0x...",
      "prediction_text": "Potential reentrancy vulnerability",
      "severity": "high",
      "description": "The contract does not properly check the return value of a call to another contract, allowing an attacker to drain funds.",
      "created_at": "2023-10-28T15:00:00Z"
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `POST /api/predictions`
        `Content-Type: application/json`
        `{
          "contract_address": "0x1234567890abcdef",
          "prediction_text": "Possible integer overflow",
          "severity": "high",
          "description": "Arithmetic operations within the contract could lead to integer overflows, potentially allowing an attacker to manipulate the contract's state."
        }`
    *   **Response:** (See JSON response above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input data        | Check request body for errors.       |
| 404      | Not Found - Resource not found          | Verify address and endpoint path.     |
| 500      | Internal Server Error                    | Server-side error - Contact API support. |
| 429      | Too Many Requests - Rate Limit Exceeded | Retry after a delay.               |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests per minute per IP address.
*   **Burst Handling:**  A small burst of requests up to 120 requests per minute will be allowed, but exceeding this limit will result in a 429 error.
*   **Rate Limit Headers:**  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response headers to indicate the current rate limit status.  Example: `X-RateLimit-Limit: 60, X-RateLimit-Remaining: 59, X-RateLimit-Reset: 1672886400`
```