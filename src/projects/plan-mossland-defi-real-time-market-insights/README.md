# Mossland Crypto Community Sentiment & Security Dashboard with AI-Driven Insights

## Project Description

Mossland Defi Real-Time Market Insights is a comprehensive platform designed to provide users with real-time sentiment analysis and security insights from the crypto community. Leveraging Ethereum blockchain transactions, this project aims at offering a more secure and data-informed trading experience.

## Features
- Sentiment Analysis Module: Data retrieval from Twitter API and basic machine learning models for text classification.
- Blockchain Integration: Real-time transactional data from Ethereum.
- Initial Target Users: 500 active users expected in the initial phase.
- Phase 2: Integration with more external APIs to enhance AI-driven insights, support for multiple blockchain networks beyond Ethereum.
- Long-term Vision: Expand into a full-fledged Web3 ecosystem offering additional services like decentralized insurance and identity verification systems.

## Tech Stack

![Next.js](https://img.shields.io/badge/nextjs-%23000000.svg?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Express.js](https://img.shields.io/badge/express-%23404d59.svg?style=for-the-badge&logo=express&logoColor=%2361DAFB)
![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Ethereum](https://img.shields.io/badge/ethereum-%23F7931A.svg?style=for-the-badge&logo=Ethereum)

## Getting Started

### Prerequisites
- Node.js and npm (or yarn) installed.

### Installation
```bash
git clone https://github.com/yourusername/plan-mossland-defi-real-time-market-insights.git
cd plan-mossland-defi-real-time-market-insights
npm install # or yarn
```

### Setup
1. Create a `.env` file in the root directory and add your API keys:
   ```bash
   NEXT_PUBLIC_TWITTER_API_KEY=your_twitter_api_key
   ETHEREUM_NODE_URL=https://mainnet.infura.io/v3/your_project_id
   ```

2. Initialize the database with necessary tables using the provided SQL scripts.

### Running the Project
```bash
npm run dev # or yarn dev
```

## Usage Examples

To start sentiment analysis:
```bash
npm run analyze-sentiment # or yarn analyze-sentiment
```

For testing blockchain integration:
```bash
npm run test-blockchain-integration # or yarn test-blockchain-integration
```

## Project Structure
- `frontend` - Contains the Next.js application.
- `backend` - Express server with API routes and business logic.
- `database` - SQL scripts for database setup and management.
- `blockchain` - Ethereum-related modules and services.

## Contributing Guidelines

1. Fork the repository on GitHub.
2. Clone your forked repository to your local machine.
3. Create a new branch for your feature or bug fix.
4. Commit changes to that branch.
5. Push your changes to your fork.
6. Open a pull request against the main repository.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.