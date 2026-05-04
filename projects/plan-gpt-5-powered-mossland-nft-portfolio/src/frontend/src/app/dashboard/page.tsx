import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';

interface PortfolioItem {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
}

interface DashboardProps {
  portfolioData: PortfolioItem[];
  marketData: any; // Replace 'any' with a specific market data interface
}

const Dashboard: React.FC<DashboardProps> = ({ portfolioData, marketData }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!portfolioData || !marketData) {
      setError('Failed to load data.');
      setLoading(false);
      return;
    }

    setLoading(true);

    // Simulate data fetching delay
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, [portfolioData, marketData]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-red-700">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex">
      {/* Portfolio Overview */}
      <div className="w-1/2 p-4">
        <h2 className="text-2xl font-bold mb-4">Portfolio Overview</h2>
        {portfolioData.length > 0 ? (
          portfolioData.map((item) => (
            <div key={item.symbol} className="mb-2 p-2 rounded-md border border-gray-300">
              <p className="font-semibold mb-1">{item.name} ({item.symbol})</p>
              <p className="text-lg font-bold">{item.quantity} units at ${item.price.toFixed(2)}</p>
            </div>
          ))
        ) : (
          <p>No portfolio data available.</p>
        )}
      </div>

      {/* Market Data Charts */}
      <div className="w-1/2 p-4">
        <h2 className="text-2xl font-bold mb-4">Market Data Charts</h2>
        {marketData && marketData.labels && marketData.datasets ? (
          <canvas
            id="marketChart"
            className="w-full h-48"
          ></canvas>
        ) : (
          <p>No market data available.</p>
        )}
      </div>

      {/* Rebalancing Controls */}
      <div className="w-full p-4">
        <h2 className="text-2xl font-bold mb-4">Rebalancing Controls</h2>
        {/* Placeholder for rebalancing controls */}
        <p>Rebalancing controls would go here.</p>
      </div>
    </div>
  );
};

export default Dashboard;