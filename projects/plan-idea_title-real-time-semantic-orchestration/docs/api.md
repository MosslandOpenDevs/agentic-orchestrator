```markdown
# Agent Communication System API Documentation

## 1. Overview

This API provides a set of endpoints for managing agents, sending messages between them, and retrieving transaction data within the Agent Communication System.  It is designed to facilitate communication and data exchange between autonomous agents.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  This key must be obtained during the initial setup process.  Authentication is crucial for security and usage tracking.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.agentsystem.com`

## 4. Endpoints

### 4.1. POST /api/agents

*   **Method:** POST
*   **Path:** /api/agents
*   **Description:** Creates a new agent in the system.  Requires a unique agent name and a short description.
*   **Request Parameters/Body:**

    ```json
    {
      "name": "AgentAlpha",
      "description": "A simple agent for testing.",
      "capabilities": ["data_analysis", "communication"]
    }
    ```

    *   `name` (string, required): The name of the agent.
    *   `description` (string, optional): A short description of the agent.
    *   `capabilities` (array, optional): An array of capabilities the agent possesses.
*   **Response Format:**

    *   **201 Created:** Returns the newly created agent object.

        ```json
        {
          "id": "agent123",
          "name": "AgentAlpha",
          "description": "A simple agent for testing.",
          "capabilities": ["data_analysis", "communication"]
        }
        ```

    *   **400 Bad Request:** Returns an error message if the request body is invalid or missing required fields.
*   **Example Request:**

    ```bash
    curl -X POST \
      https://api.agentsystem.com/api/agents \
      -H 'Content-Type: application/json' \
      -H 'X-API-Key: YOUR_API_KEY' \
      -d '{
        "name": "AgentBeta",
        "description": "Another agent",
        "capabilities": ["data_processing"]
      }'
    ```

*   **Example Response (201 Created):**

    ```json
    {
      "id": "agent456",
      "name": "AgentBeta",
      "description": "Another agent",
      "capabilities": ["data_processing"]
    }
    ```

### 4.2. GET /api/agents/:agentId

*   **Method:** GET
*   **Path:** /api/agents/{agentId}
*   **Description:** Retrieves agent details by ID.
*   **Request Parameters/Body:** None
*   **Response Format:**

    *   **200 OK:** Returns the agent object.

        ```json
        {
          "id": "agent123",
          "name": "AgentAlpha",
          "description": "A simple agent for testing.",
          "capabilities": ["data_analysis", "communication"]
        }
        ```

    *   **404 Not Found:** Returns an error message if the agent with the specified ID does not exist.
*   **Example Request:**

    ```bash
    curl -X GET \
      https://api.agentsystem.com/api/agents/agent123 \
      -H 'X-API-Key: YOUR_API_KEY'
    ```

*   **Example Response (200 OK):**

    ```json
    {
      "id": "agent123",
      "name": "AgentAlpha",
      "description": "A simple agent for testing.",
      "capabilities": ["data_analysis", "communication"]
    }
    ```

### 4.3. POST /api/messages

*   **Method:** POST
*   **Path:** /api/messages
*   **Description:** Sends a message between agents.  Requires the recipient agent's ID and the message content.
*   **Request Parameters/Body:**

    ```json
    {
      "recipientId": "agent456",
      "content": "Hello AgentBeta, this is a test message."
    }
    ```

    *   `recipientId` (string, required): The ID of the agent to send the message to.
    *   `content` (string, required): The message content.
*   **Response Format:**

    *   **201 Created:** Returns a confirmation object.

        ```json
        {
          "messageId": "message789",
          "timestamp": "2023-10-27T10:00:00Z",
          "recipientId": "agent456",
          "content": "Hello AgentBeta, this is a test message."
        }
        ```

    *   **400 Bad Request:** Returns an error message if the request body is invalid or missing required fields.
    *   **404 Not Found:** Returns an error message if the recipient agent does not exist.
*   **Example Request:**

    ```bash
    curl -X POST \
      https://api.agentsystem.com/api/messages \
      -H 'Content-Type: application/json' \
      -H 'X-API-Key: YOUR_API_KEY' \
      -d '{
        "recipientId": "agent456",
        "content": "This is a message to AgentBeta."
      }'
    ```

*   **Example Response (201 Created):**

    ```json
    {
      "messageId": "message789",
      "timestamp": "2023-10-27T10:00:00Z",
      "recipientId": "agent456",
      "content": "Hello AgentBeta, this is a test message."
    }
    ```

### 4.4. GET /api/transactions

*   **Method:** GET
*   **Path:** /api/transactions
*   **Description:** Retrieves transaction data.  This endpoint may return a list of transactions or a summary of transaction data.  The specific format depends on the system implementation.
*   **Request Parameters/Body:** None
*   **Response Format:**

    *   **200 OK:** Returns a list of transaction objects.

        ```json
        [
          {
            "transactionId": "transaction1",
            "timestamp": "2023-10-26T12:00:00Z",
            "agentId": "agent123",
            "amount": 10.50
          },
          {
            "transactionId": "transaction2",
            "timestamp": "2023-10-26T12:05:00Z",
            "agentId": "agent456",
            "amount": 5.25
          }
        ]
        ```

    *   **200 OK (Summary):** Returns a summary of transaction data (e.g., total amount, number of transactions).

        ```json
        {
          "totalAmount": 15.75,
          "numberOfTransactions": 2
        }
        ```
*   **Example Request:**

    ```bash
    curl -X GET \
      https://api.agentsystem.com/api/transactions \
      -H 'X-API-Key: YOUR_API_KEY'
    ```

*   **Example Response (200 OK - List):**

    ```json
    [
      {
        "transactionId": "transaction1",
        "timestamp": "2023-10-26T12:00:00Z",
        "agentId": "agent123",
        "amount": 10.50
      },
      {
        "transactionId": "transaction2",
        "timestamp": "2023-10-26T12:05:00Z",
        "agentId": "agent456",
        "amount": 5.25
      }
    ]
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid request body.      |
| 401      | Unauthorized - Invalid API key.          |
| 404      | Not Found - Resource not found.           |
| 500      | Internal Server Error - Server error.     |

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:** Rate limit information will be returned in the response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
*   **Example:** `X-RateLimit-Limit: 100, X-RateLimit-Remaining: 85, X-RateLimit-Reset: 60`
```