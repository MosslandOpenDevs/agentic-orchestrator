```markdown
# Smart Contract Risk Assessment API Documentation

## 1. Overview

This API provides access to data related to smart contracts and their associated risk scores. It allows you to retrieve a list of contracts, details for individual contracts, and their corresponding risk scores. This information can be used for portfolio analysis, risk management, and investment decision-making.

## 2. Authentication Details

Currently, this API does not require authentication. All requests are publicly accessible.  Future versions may require API keys or other authentication mechanisms.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`

## 4. Endpoints

### 4.1 GET /api/contracts

*   **Method:** GET
*   **Path:** /api/contracts
*   **Description:** Retrieves a list of smart contracts.  Returns a JSON array of contract objects.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
*   **Example Request:**
    `GET /api/contracts`
*   **Example Response:**

    ```json
    [
      {
        "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
        "contractName": "MyToken",
        "creationDate": "2023-10-26T10:00:00Z",
        "totalSupply": 1000000,
        "decimals": 18
      },
      {
        "contractAddress": "0x9876543210fedcba9876543210fedcba98765432",
        "contractName": "StableCoin",
        "creationDate": "2023-10-27T14:30:00Z",
        "totalSupply": 1000000000,
        "decimals": 18
      }
    ]
    ```

### 4.2 GET /api/contracts/{contractAddress}

*   **Method:** GET
*   **Path:** /api/contracts/{contractAddress}
*   **Description:** Retrieves details for a specific smart contract.  Replace `{contractAddress}` with the actual contract address.
*   **Request Parameters/Body:**
    *   `contractAddress` (path parameter): The address of the smart contract.  Must be a valid Ethereum address.
*   **Response Format:** JSON Object
*   **Example Request:**
    `GET /api/contracts/0x1234567890abcdef1234567890abcdef12345678`
*   **Example Response:**

    ```json
    {
      "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "contractName": "MyToken",
      "creationDate": "2023-10-26T10:00:00Z",
      "totalSupply": 1000000,
      "decimals": 18,
      "owner": "0xSomeOtherAddress"
    }
    ```

### 4.3 GET /api/riskscores

*   **Method:** GET
*   **Path:** /api/riskscores
*   **Description:** Retrieves a list of risk scores.  Returns a JSON array of risk score objects.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
*   **Example Request:**
    `GET /api/riskscores`
*   **Example Response:**

    ```json
    [
      {
        "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
        "riskScore": 75
      },
      {
        "contractAddress": "0x9876543210fedcba9876543210fedcba98765432",
        "riskScore": 30
      }
    ]
    ```

### 4.4 GET /api/riskscore/{contractAddress}

*   **Method:** GET
*   **Path:** /api/riskscore/{contractAddress}
*   **Description:** Retrieves the risk score for a specific smart contract.  Replace `{contractAddress}` with the actual contract address.
*   **Request Parameters/Body:**
    *   `contractAddress` (path parameter): The address of the smart contract. Must be a valid Ethereum address.
*   **Response Format:** JSON Object
*   **Example Request:**
    `GET /api/riskscore/0x1234567890abcdef1234567890abcdef12345678`
*   **Example Response:**

    ```json
    {
      "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "riskScore": 75
    }
    ```

## 5. Error Codes and Handling

| HTTP Status Code | Error Code | Description                               |
|------------------|------------|-------------------------------------------|
| 400              | INVALID_REQUEST | The request was malformed or invalid.    |
| 404              | CONTRACT_NOT_FOUND | The specified contract address does not exist. |
| 500              | INTERNAL_SERVER_ERROR | An unexpected error occurred on the server. |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure stability.

*   **Limit:** 100 requests per minute per IP address.
*   **Headers:**  Rate limiting information will be returned in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

    *   `X-RateLimit-Limit`: The maximum number of requests allowed in the time window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the time window.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```