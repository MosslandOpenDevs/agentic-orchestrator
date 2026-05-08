import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface PortfolioItem {
  tokenId: string;
  name: string;
  value: number;
  imageURL: string;
}

interface RiskAssessment {
  overallRisk: string;
  details: string;
}

interface PortfolioDashboardProps {
  initialPortfolio: PortfolioItem[];
  riskAssessmentData: RiskAssessment;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialPortfolio, riskAssessmentData }) => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>(initialPortfolio);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 1500);
  }, []);

  const handleRebalance = () => {
    router.push('/rebalance');
  };

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4">Portfolio Dashboard</h1>
        <p className="text-gray-600">Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4">Portfolio Dashboard</h1>
        <p className="text-red-600">Error loading data: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* Portfolio Value */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">Portfolio Value</h2>
        <p className="text-gray-700">Total Value: ${portfolio.reduce((sum, item) => sum + item.value, 0)}</p>
      </div>

      {/* Portfolio Items */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {portfolio.map((item) => (
          <div
            key={item.tokenId}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300"
            aria-label={`NFT: ${item.name}`}
          >
            <img src={item.imageURL} alt={item.name} className="w-full h-48 object-cover rounded-lg mb-2" />
            <p className="text-xl font-semibold text-gray-800">{item.name}</p>
            <p className="text-gray-700">${item.value}</p>
          </div>
        ))}
      </div>

      {/* Risk Assessment */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">Risk Assessment</h2>
        <p className="text-gray-700">{riskAssessmentData.overallRisk}</p>
        <p className="text-gray-700">{riskAssessmentData.details}</p>
      </div>

      {/* Rebalancing Button */}
      <button
        onClick={handleRebalance}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
        aria-label="Rebalance Portfolio"
      >
        Rebalance Portfolio
      </button>
    </div>
  );
};

export default PortfolioDashboard;