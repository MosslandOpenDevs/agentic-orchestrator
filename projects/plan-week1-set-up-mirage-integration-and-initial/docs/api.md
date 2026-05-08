```markdown
# DAO Strategy Simulation API Documentation

## 1. Overview

This API provides endpoints for managing and simulating DAO strategies. It allows users to retrieve a list of strategies, fetch details of a specific strategy, initiate simulation runs, and retrieve simulation results. This API is designed to be used by developers building tools and applications that interact with and analyze DAO strategy performance.

## 2. Authentication Details

This API uses API key authentication.  You must include your API key in the `X-API-Key` header for all requests.  Contact your administrator to obtain an API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`  (Replace with your actual API base URL)

## 4. Endpoints

### 4.1 GET /api/strategies

*   **Method:** `GET`
*   **Path:** `/api/strategies`
*   **Description:** Retrieves a list of all DAO strategies.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each object in the array represents a DAO strategy and includes the following fields:
        *   `strategyId`: (String) Unique identifier for the strategy.
        *   `name`: (String) Name of the strategy.
        *   `description`: (String) Description of the strategy.
        *   `parameters`: (Object)  A JSON object containing the strategy's parameters.
*   **Example Request:**

    `GET /api/strategies`
*   **Example Response:**

    ```json
    [
      {
        "strategyId": "strat-123",
        "name": "Aggressive Growth",
        "description": "A strategy focused on maximizing returns.",
        "parameters": {
          "riskLevel": "high",
          "investmentHorizon": "short",
          "allocation": {
            "tokenA": 0.6,
            "tokenB": 0.4
          }
        }
      },
      {
        "strategyId": "strat-456",
        "name": "Conservative Hold",
        "description": "A strategy focused on preserving capital.",
        "parameters": {
          "riskLevel": "low",
          "investmentHorizon": "long",
          "allocation": {
            "tokenA": 0.8,
            "tokenB": 0.2
          }
        }
      }
    ]
    ```

### 4.2 GET /api/strategies/:strategyId

*   **Method:** `GET`
*   **Path:** `/api/strategies/:strategyId`
*   **Description:** Retrieves a specific DAO strategy by ID.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    *   The response will contain the details of the strategy with the specified `strategyId`.
*   **Example Request:**

    `GET /api/strategies/strat-123`
*   **Example Response:**

    ```json
    {
      "strategyId": "strat-123",
      "name": "Aggressive Growth",
      "description": "A strategy focused on maximizing returns.",
      "parameters": {
        "riskLevel": "high",
        "investmentHorizon": "short",
        "allocation": {
          "tokenA": 0.6,
          "tokenB": 0.4
        }
      }
    }
    ```

### 4.3 POST /api/simulations

*   **Method:** `POST`
*   **Path:** `/api/simulations`
*   **Description:** Initiates a new simulation run for a given DAO strategy.
*   **Request Parameters/Body:** JSON
    *   `strategyId`: (String) The ID of the strategy to simulate.
    *   `parameters`: (Object) A JSON object containing the parameters for the simulation.  This should match the parameters defined for the strategy.
    *   `duration`: (Integer) The duration of the simulation in days.
*   **Response Format:** JSON
    *   On success, the response will contain the simulation ID.
    *   On error, see Error Codes and Handling.
*   **Example Request:**

    ```json
    POST /api/simulations
    Content-Type: application/json

    {
      "strategyId": "strat-123",
      "parameters": {
        "riskLevel": "high",
        "investmentHorizon": "short"
      },
      "duration": 30
    }
    ```
*   **Example Response (Success):**

    ```json
    {
      "simulationId": "sim-789"
    }
    ```

### 4.4 GET /api/simulation-results

*   **Method:** `GET`
*   **Path:** `/api/simulation-results`
*   **Description:** Retrieves a list of all simulation results.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each object in the array represents a simulation result and includes the following fields:
        *   `simulationId`: (String) Unique identifier for the simulation.
        *   `strategyId`: (String) The ID of the strategy that was simulated.
        *   `startTime`: (Timestamp) The start time of the simulation.
        *   `endTime`: (Timestamp) The end time of the simulation.
        *   `results`: (Object) A JSON object containing the simulation results (e.g., returns, volatility).
*   **Example Request:**

    `GET /api/simulation-results`
*   **Example Response:**

    ```json
    [
      {
        "simulationId": "sim-789",
        "strategyId": "strat-123",
        "startTime": "2023-10-26T10:00:00Z",
        "endTime": "2023-10-29T10:00:00Z",
        "results": {
          "averageReturn": 0.15,
          "volatility": 0.20
        }
      },
      {
        "simulationId": "sim-101",
        "strategyId": "strat-456",
        "startTime": "2023-10-27T12:00:00Z",
        "endTime": "2023-10-30T12:00:00Z",
        "results": {
          "averageReturn": 0.05,
          "volatility": 0.10
        }
      }
    ]
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Response Format     |
| :------ | :--------------------------------------- | :------------------ |
| 400      | Bad Request - Invalid input parameters. | JSON: { "error": "message" } |
| 401      | Unauthorized - Invalid API key.        | JSON: { "error": "invalid_api_key" } |
| 404      | Not Found - Strategy or simulation not found. | JSON: { "error": "resource_not_found" } |
| 500      | Internal Server Error - Server error.    | JSON: { "error": "internal_server_error" } |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.  The rate limit is 100 requests per minute per API key.  If you exceed the rate limit, you will receive a 429 Too Many Requests error.  The response headers will include rate limit information, including the remaining requests and the reset time.  Example: `X-RateLimit-Remaining: 90`, `X-RateLimit-Reset: 60`.
```