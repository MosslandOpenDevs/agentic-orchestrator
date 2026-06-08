import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart } from 'chart.js';

// Define interfaces for data
interface PortfolioData {
  assets: {
    [key: string]: {
      name: string;
      quantity: number;
      price: number;
    };
  };
  riskScore: number;
  recommendations: string[];
}

interface NFTPosition {
  tokenId: string;
  quantity: number;
  price: number;
}

interface DashboardProps {
  data?: PortfolioData;
  nftPositions?: NFTPosition[];
}

const Dashboard: React.FC<DashboardProps> = ({ data, nftPositions }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!data) {
      setLoading(false);
      setError('No portfolio data available.');
      return;
    }

    setLoading(false);
    setError(null);
  }, [data]);

  useEffect(() => {
    if (nftPositions && nftPositions.length > 0) {
      // Placeholder for NFT position details - replace with actual data fetching
      // Example: fetchNFTPositions(nftPositions);
    }
  }, [nftPositions]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md text-red-700">
        <p>Error: {error}</p>
      </div>
    );
  }

  const portfolioSummary = data;
  const riskScore = portfolioSummary?.riskScore || 0;
  const recommendations = portfolioSummary?.recommendations || [];

  // Placeholder for risk visualization - replace with Chart.js
  const riskVisualization = (
    <div className="w-full h-48 rounded-lg shadow-md bg-gray-200 flex items-center justify-center">
      <p>Risk Visualization - Placeholder</p>
    </div>
  );

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* Portfolio Summary */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-2">Portfolio Summary</h2>
        {portfolioSummary && Object.keys(portfolioSummary.assets).map((assetKey) => (
          <div key={assetKey} className="mb-2 flex items-center justify-between">
            <span className="text-gray-700">{portfolioSummary.assets[assetKey].name}</span>
            <span className="text-gray-700">{portfolioSummary.assets[assetKey].quantity}</span>
          </div>
        ))}
        <p className="text-gray-600">Risk Score: {riskScore}</p>
        <p className="text-gray-600">Recommendations: {recommendations.join(', ')}</p>
      </div>

      {/* Risk Visualization */}
      {riskVisualization}

      {/* Rebalancing Recommendations */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-2">Rebalancing Recommendations</h2>
        <p>Placeholder for rebalancing recommendations.</p>
      </div>

      {/* NFT Position Details */}
      <div className="mb-4 bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-2">NFT Position Details</h2>
        {nftPositions && nftPositions.map((position) => (
          <div key={position.tokenId} className="mb-2 flex items-center justify-between">
            <span className="text-gray-700">{position.tokenId}</span>
            <span className="text-gray-700">{position.quantity}</span>
            <span className="text-gray-700">{position.price}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;