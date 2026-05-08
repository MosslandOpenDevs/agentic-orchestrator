```markdown
# NFT Portfolio & AI Risk Assessment API Documentation

## 1. Overview

This API provides access to data and services for NFT portfolio analysis and risk assessment, leveraging AI-powered tools for smart contract generation and more. It offers endpoints for retrieving NFT price data, accessing NFT metadata, generating risk assessments, and utilizing a GPT-5 API for advanced tasks.

## 2. Authentication Details

All API endpoints require an API key for authentication.  This key should be passed in the `X-API-Key` header of each request.  Contact your administrator to obtain your API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com` (Replace with your actual base URL)

## 4. Endpoints

### 4.1. GET /api/nft/price

*   **Method:** GET
*   **Path:** /api/nft/price
*   **Description:** Retrieves the current price of an NFT based on its contract address and token ID.
*   **Request Parameters:**
    *   `contract_address` (string, required): The Ethereum contract address of the NFT.  Example: `0xabc...def`
    *   `token_id` (string, required): The token ID of the NFT. Example: `123`
*   **Response Format:** JSON
    *   `price` (number): The current price of the NFT in the specified currency (default: USD).
    *   `currency` (string, optional): The currency to display the price in (e.g., USD, EUR, GBP). Defaults to USD.
    *   `timestamp` (string): The timestamp of the price reading.
*   **Example Request:**

    ```
    GET /api/nft/price?contract_address=0xabc1234567890abcdef1234567890abcdef12345678&token_id=1
    ```
*   **Example Response:**

    ```json
    {
      "price": 2500.50,
      "currency": "USD",
      "timestamp": "2023-10-27T10:30:00Z"
    }
    ```

### 4.2. GET /api/nft/data

*   **Method:** GET
*   **Path:** /api/nft/data
*   **Description:** Retrieves NFT metadata based on its contract address and token ID.
*   **Request Parameters:**
    *   `contract_address` (string, required): The Ethereum contract address of the NFT. Example: `0xabc...def`
    *   `token_id` (string, required): The token ID of the NFT. Example: `123`
*   **Response Format:** JSON
    *   `name` (string): The name of the NFT.
    *   `symbol` (string): The symbol of the NFT.
    *   `description` (string): A description of the NFT.
    *   `image_url` (string): URL to the NFT's image.
    *   `attributes` (array): An array of NFT attributes.
    *   `token_id` (string): The token ID of the NFT.
*   **Example Request:**

    ```
    GET /api/nft/data?contract_address=0xabc1234567890abcdef1234567890abcdef12345678&token_id=1
    ```
*   **Example Response:**

    ```json
    {
      "name": "My Awesome NFT",
      "symbol": "MAN",
      "description": "A truly amazing NFT!",
      "image_url": "https://example.com/images/man.png",
      "attributes": [
        {"trait_type": "Rarity", "value": "Rare"},
        {"trait_type": "Color", "value": "Blue"}
      ],
      "token_id": "1"
    }
    ```

### 4.3. POST /api/risk/assessment

*   **Method:** POST
*   **Path:** /api/risk/assessment
*   **Description:** Generates a risk assessment for a portfolio of NFTs based on various factors.
*   **Request Body:** JSON
    *   `nft_addresses` (array, required): An array of Ethereum contract addresses of the NFTs in the portfolio. Example: `["0xabc...def", "0xdef...abc"]`
    *   `portfolio_value` (number, required): The total value of the portfolio in USD.
    *   `risk_tolerance` (string, required): The user's risk tolerance (e.g., "low", "medium", "high").
*   **Response Format:** JSON
    *   `risk_score` (number): A numerical score representing the overall risk of the portfolio.
    *   `risk_level` (string): The risk level based on the risk score (e.g., "low", "medium", "high").
    *   `recommendations` (array): An array of recommendations for managing the portfolio risk.
*   **Example Request:**

    ```json
    POST /api/risk/assessment
    {
      "nft_addresses": ["0xabc1234567890abcdef1234567890abcdef12345678", "0xdef1234567890abcdef1234567890abcdef12345678"],
      "portfolio_value": 10000,
      "risk_tolerance": "medium"
    }
    ```
*   **Example Response:**

    ```json
    {
      "risk_score": 65,
      "risk_level": "medium",
      "recommendations": [
        "Diversify your NFT portfolio.",
        "Consider reducing exposure to high-volatility NFTs."
      ]
    }
    ```

### 4.4. GET /api/gpt/generate

*   **Method:** GET
*   **Path:** /api/gpt/generate
*   **Description:** Calls the GPT-5 API for smart contract generation or other tasks.  This endpoint is currently a placeholder and may not be functional.
*   **Request Parameters:**
    *   `task` (string, required): The task to be performed by the GPT-5 API (e.g., "generate_smart_contract", "summarize_nft_data").
    *   `prompt` (string, optional):  A prompt to guide the GPT-5 API.
*   **Response Format:** JSON
    *   `result` (string): The result of the GPT-5 API call.
    *   `status` (string):  "success" or "error".
*   **Example Request:**

    ```
    GET /api/gpt/generate?task=generate_smart_contract&prompt="Create a simple ERC-20 token contract"
    ```
*   **Example Response (Success):**

    ```json
    {
      "result": "Here's a basic ERC-20 token contract...",
      "status": "success"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters  | Check request parameters for correctness. |
| 401      | Unauthorized - Missing or invalid API key | Provide a valid API key in the header. |
| 404      | Not Found - Resource not found          | Verify the resource exists and the parameters are correct. |
| 500      | Internal Server Error                    | Contact support for assistance.       |
| 503      | Service Unavailable - API unavailable     | Try again later.                     |

## 6. Rate Limiting

This API is subject to rate limiting to prevent abuse.

*   **Requests per minute:** 60 requests
*   **Burst Limit:** 120 requests (after which, requests are throttled)
*   **Throttling:**  If the rate limit is exceeded, the API will return a 429 (Too Many Requests) error.  The response header will include a `Retry-After` value indicating when the client can retry the request.

```
Retry-After: 60
```
```
