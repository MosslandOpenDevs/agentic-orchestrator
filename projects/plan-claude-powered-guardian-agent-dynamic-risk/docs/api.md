```markdown
# Portfolio & Risk Management API Documentation

## 1. Overview

This API provides access to portfolio management tools and risk profiling capabilities. It allows users to retrieve their portfolio data, create new portfolios, view risk profiles, and access strategic recommendations.  This documentation outlines the available endpoints, authentication requirements, and expected response formats.

## 2. Authentication Details

All API requests require a valid API key in the `X-API-Key` header.  This key is provided upon successful registration and should be kept confidential.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual base URL)

## 4. Endpoints

### 4.1. GET /api/portfolio

*   **Method:** `GET`
*   **Path:** `/api/portfolio`
*   **Description:** Retrieves portfolio data for a given NFT holder.  This endpoint requires the user's NFT holder address to retrieve their associated portfolio.
*   **Request Parameters/Body:**
    *   `nft_holder_address` (string, required): The Ethereum address of the NFT holder.
*   **Response Format:** JSON
    ```json
    {
      "success": true,
      "portfolio": {
        "portfolio_id": "string",
        "user_id": "string",
        "total_value": "number",
        "asset_allocation": {
          "crypto": {
            "btc": {"percentage": 30, "value": 10000},
            "eth": {"percentage": 20, "value": 5000}
          },
          "defi": {"percentage": 10, "value": 3000},
          "stablecoins": {"percentage": 40, "value": 8000}
        },
        "last_updated": "timestamp"
      }
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/portfolio?nft_holder_address=0xd8dA6611E982AC279809Ec450170BFC3dC1dBD94`
    *   **Response:** (Example - actual values will vary)
        ```json
        {
          "success": true,
          "portfolio": {
            "portfolio_id": "portfolio123",
            "user_id": "user456",
            "total_value": 25000,
            "asset_allocation": {
              "crypto": {
                "btc": {"percentage": 30, "value": 7500},
                "eth": {"percentage": 20, "value": 5000}
              },
              "defi": {"percentage": 10, "value": 3000},
              "stablecoins": {"percentage": 40, "value": 8000}
            },
            "last_updated": "2024-10-27T10:00:00Z"
          }
        }
        ```

### 4.2. POST /api/portfolio

*   **Method:** `POST`
*   **Path:** `/api/portfolio`
*   **Description:** Creates a new portfolio.
*   **Request Parameters/Body:**
    *   `user_id` (string, required): The ID of the user creating the portfolio.
    *   `asset_allocation` (JSON, required):  An object defining the desired asset allocation. Example:
        ```json
        {
          "crypto": {
            "btc": {"percentage": 50, "value": 10000},
            "eth": {"percentage": 50, "value": 10000}
          },
          "defi": {"percentage": 0, "value": 0},
          "stablecoins": {"percentage": 0, "value": 0}
        }
        ```
*   **Response Format:** JSON
    ```json
    {
      "success": true,
      "portfolio": {
        "portfolio_id": "string",
        "user_id": "string",
        "total_value": "number",
        "asset_allocation": { ... },
        "last_updated": "timestamp"
      }
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `POST /api/portfolio`
        `Content-Type: application/json`
        `X-API-Key: YOUR_API_KEY`
        `Body: { "user_id": "user789", "asset_allocation": { "crypto": { "btc": {"percentage": 20, "value": 5000}, "eth": {"percentage": 80, "value": 4000} } } }`
    *   **Response:** (Example - actual values will vary)
        ```json
        {
          "success": true,
          "portfolio": {
            "portfolio_id": "portfolio789",
            "user_id": "user789",
            "total_value": 9000,
            "asset_allocation": {
              "crypto": {
                "btc": {"percentage": 20, "value": 5000},
                "eth": {"percentage": 80, "value": 4000}
              },
              "defi": {"percentage": 0, "value": 0},
              "stablecoins": {"percentage": 0, "value": 0}
            },
            "last_updated": "2024-10-27T10:30:00Z"
          }
        }
        ```

### 4.3. GET /api/riskProfile

*   **Method:** `GET`
*   **Path:** `/api/riskProfile`
*   **Description:** Retrieves a risk profile.  This endpoint may require user input to determine the appropriate risk profile.
*   **Request Parameters/Body:**
    *   `risk_tolerance` (string, optional): User's risk tolerance level (e.g., "conservative", "moderate", "aggressive"). Defaults to "moderate".
*   **Response Format:** JSON
    ```json
    {
      "success": true,
      "risk_profile": {
        "risk_tolerance": "string",
        "investment_horizon": "string",
        "asset_allocation_recommendation": { ... }
      }
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/riskProfile?risk_tolerance=aggressive`
    *   **Response:** (Example - actual values will vary)
        ```json
        {
          "success": true,
          "risk_profile": {
            "risk_tolerance": "aggressive",
            "investment_horizon": "short-term",
            "asset_allocation_recommendation": {
              "crypto": {"percentage": 70, "value": 10000},
              "defi": {"percentage": 10, "value": 3000},
              "stablecoins": {"percentage": 20, "value": 5000}
            }
          }
        }
        ```

### 4.4. GET /api/strategy

*   **Method:** `GET`
*   **Path:** `/api/strategy`
*   **Description:** Retrieves a strategy.  This endpoint may provide recommendations based on portfolio holdings and risk profile.
*   **Request Parameters/Body:**
    *   None
*   **Response Format:** JSON
    ```json
    {
      "success": true,
      "strategy": {
        "strategy_name": "string",
        "description": "string",
        "recommendations": [
          "string",
          "string"
        ]
      }
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/strategy`
    *   **Response:** (Example - actual values will vary)
        ```json
        {
          "success": true,
          "strategy": {
            "strategy_name": "Dynamic Portfolio Rebalancing",
            "description": "Automatically adjusts portfolio allocation based on market conditions.",
            "recommendations": [
              "Consider increasing exposure to DeFi assets during periods of high growth.",
              "Reduce exposure to crypto assets during periods of market volatility."
            ]
          }
        }
        ```

## 5. Error Codes and Handling

| Code    | Description                               | Response Body                                                              |
| :------ | :---------------------------------------- | :------------------------------------------------------------------------ |
| 400      | Bad Request - Invalid Input               | `{"success": false, "error": "Invalid input provided"}`                    |
| 401      | Unauthorized - Invalid API Key            | `{"success": false, "error": "Invalid API key"}`                           |
| 404      | Not Found - Resource Not Found            | `{"success": false, "error": "Resource not found"}`                        |
| 500      | Internal Server Error                    | `{"success": false, "error": "Internal server error"}`                    |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for short bursts of activity)
*   **Reset Time:** 60 seconds

Exceeding the rate limits will result in a `429 Too Many Requests` error.  Implement retry logic with exponential backoff to handle these errors gracefully.  Consult the API documentation for more details on rate limiting and error handling.
```