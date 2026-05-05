import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useDisclosure } from 'next/hooks';

// Define interfaces for data models
interface PortfolioItem {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
}

interface RebalancingRecommendation {
  asset: string;
  percentage: number;
}

interface RiskTolerance {
  conservative: boolean;
  moderate: boolean;
  aggressive: boolean;
}

const Dashboard = () => {
  const router = useRouter();
  const [portfolioData, setPortfolioData] = useState<PortfolioItem[] | null>(null);
  const [rebalancingRecommendations, setRebalancingRecommendations] = useState<RebalancingRecommendation[] | null>(null);
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Simulate fetching data (replace with actual API calls)
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate fetching portfolio data
        const portfolio: PortfolioItem[] = [
          { symbol: 'AAPL', name: 'Apple Inc.', quantity: 100, price: 170 },
          { symbol: 'MSFT', name: 'Microsoft Corp.', quantity: 50, price: 300 },
          { symbol: 'GOOG', name: 'Alphabet Inc.', quantity: 25, price: 2500 },
        ];
        setPortfolioData(portfolio);

        // Simulate fetching rebalancing recommendations
        const recommendations: RebalancingRecommendation[] = [
          { asset: 'GOOG', percentage: 10 },
          { asset: 'AAPL', percentage: 5 },
        ];
        setRebalancingRecommendations(recommendations);

        // Simulate fetching risk tolerance
        setRiskTolerance({ conservative: false, moderate: true, aggressive: false });

        setIsLoading(false);
      } catch (err) {
        setError('Failed to load data. Please try again.');
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle navigation (example)
  const handleNavigate = (path: string) => {
    router.push(path);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <header className="text-center mb-4">
        <h1>Portfolio Dashboard</h1>
      </header>

      <section className="mb-8">
        <h2>Portfolio Overview</h2>
        {isLoading ? (
          <p>Loading portfolio data...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          portfolioData &&
          portfolioData.map((item) => (
            <div key={item.symbol} className="mb-2 p-4 bg-white rounded shadow-md">
              <h3 className="text-lg font-semibold mb-2">{item.name}</h3>
              <p className="text-gray-700">Symbol: {item.symbol}</p>
              <p className="text-gray-700">Quantity: {item.quantity}</p>
              <p className="text-gray-700">Price: ${item.price}</p>
            </div>
          ))
        )}
      </section>

      <section className="mb-8">
        <h2>Rebalancing Recommendations</h2>
        {isLoading ? (
          <p>Loading rebalancing recommendations...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          rebalancingRecommendations &&
          rebalancingRecommendations.map((recommendation) => (
            <div key={recommendation.asset} className="mb-2 p-4 bg-white rounded shadow-md">
              <p className="text-lg font-semibold mb-2">{recommendation.asset}</p>
              <p className="text-gray-700">Recommended Percentage: {recommendation.percentage}%</p>
            </div>
          ))
        )}
      </section>

      <section className="mb-8">
        <h2>Risk Tolerance Settings</h2>
        {isLoading ? (
          <p>Loading risk tolerance settings...</p>
        ) : error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          riskTolerance && (
            <p className="text-gray-700">
              Conservative: {riskTolerance.conservative ? 'Yes' : 'No'} | Moderate: {riskTolerance.moderate ? 'Yes' : 'No'} | Aggressive: {riskTolerance.aggressive ? 'Yes' : 'No'}
            </p>
          )
        )}
      </section>

      <footer className="text-center mt-4">
        <button onClick={() => handleNavigate('/settings')} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Go to Settings
        </button>
      </footer>
    </div>
  );
};

export default Dashboard;