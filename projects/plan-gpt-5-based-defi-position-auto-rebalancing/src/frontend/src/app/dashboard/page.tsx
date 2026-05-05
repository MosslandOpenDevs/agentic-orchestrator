import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { useRouter } from 'next/router';

// Define interfaces for data models
interface PortfolioData {
  assets: {
    [asset: string]: {
      name: string;
      quantity: number;
      price: number;
    };
  };
}

interface RebalancingRecommendation {
  asset: string;
  percentage: number;
}

interface RiskTolerance {
  riskLevel: 'low' | 'medium' | 'high';
  timeHorizon: 'short' | 'medium' | 'long';
}

// Dummy data for demonstration - Replace with actual API calls
const dummyPortfolioData: PortfolioData = {
  assets: {
    'BTC': { name: 'Bitcoin', quantity: 10, price: 30000 },
    'ETH': { name: 'Ethereum', quantity: 5, price: 2000 },
    'USDT': { name: 'Tether USD', quantity: 1000, price: 1 },
  },
};

const dummyRebalancingRecommendations: RebalancingRecommendation[] = [
  { asset: 'BTC', percentage: 10 },
  { asset: 'ETH', percentage: 5 },
];

const dummyRiskTolerance: RiskTolerance = {
  riskLevel: 'medium',
  timeHorizon: 'medium',
};

const Dashboard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const router = useRouter();
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [rebalancingRecommendations, setRebalancingRecommendations] = useState<RebalancingRecommendation[] | null>(null);
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance | null>(dummyRiskTolerance);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setPortfolioData(dummyPortfolioData);
      setRebalancingRecommendations(dummyRebalancingRecommendations);
      setLoading(false);
    }, 500);
  }, []);

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedRiskLevel = event.target.value;
    setRiskTolerance({ ...riskTolerance, riskLevel: selectedRiskLevel });
  };

  const handleNavigate = (asset: string) => {
    router.push(`/asset/${asset}`);
  };

  if (loading) {
    return <div>Loading Dashboard...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* Portfolio Overview */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Asset Allocation</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {portfolioData?.assets &&
              Object.values(portfolioData.assets).map((asset) => (
                <tr key={asset.name}>
                  <td>{asset.name}</td>
                  <td>{asset.quantity}</td>
                  <td>${asset.price}</td>
                  <td>${asset.quantity * asset.price}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Rebalancing Recommendations */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Rebalancing Recommendations</h2>
        <ul className="list-disc pl-5">
          {rebalancingRecommendations &&
            rebalancingRecommendations.map((recommendation) => (
              <li key={recommendation.asset}>
                {recommendation.asset} - {recommendation.percentage}%
              </li>
            ))}
        </ul>
      </div>

      {/* Risk Tolerance Settings */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Risk Tolerance</h2>
        <label htmlFor="riskLevel">Risk Level:</label>
        <select
          id="riskLevel"
          value={riskTolerance.riskLevel}
          onChange={handleRiskToleranceChange}
          aria-label="Select Risk Level"
          className="mt-2 px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>

        <label htmlFor="timeHorizon">Time Horizon:</label>
        <select
          id="timeHorizon"
          value={riskTolerance.timeHorizon}
          onChange={(event) => setRiskTolerance({ ...riskTolerance, timeHorizon: event.target.value })}
          aria-label="Select Time Horizon"
          className="mt-2 px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="long">Long</option>
        </select>
      </div>

      {/* Placeholder for future features */}
      <div className="text-gray-600 text-center mt-8">
        <p>Future features will be added here.</p>
      </div>
    </div>
  );
};

export default Dashboard;