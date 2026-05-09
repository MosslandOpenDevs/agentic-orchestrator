import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface PortfolioHolding {
  name: string;
  quantity: number;
  price: number;
}

interface PortfolioOverviewProps {
  holdings: PortfolioHolding[];
  totalValue: number;
  riskScore: number;
}

const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ holdings, totalValue, riskScore }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const userId = searchParams.get('userId') || 'defaultUser'; // Example: Fetch user data based on URL parameter

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <h2 className="text-2xl font-bold text-gray-800">Portfolio Overview</h2>
        <p className="text-gray-600">Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <h2 className="text-2xl font-bold text-red-800">Error</h2>
        <p className="text-gray-600">Failed to load portfolio data: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
      <h2 className="text-2xl font-bold text-gray-800">Portfolio Overview</h2>

      <div className="mt-4 flex flex-col items-start">
        {holdings.map((holding) => (
          <div key={holding.name} className="mb-2 bg-white p-4 rounded shadow-sm">
            <h3 className="text-xl font-semibold text-gray-800">{holding.name}</h3>
            <p className="text-gray-600">Quantity: {holding.quantity}</p>
            <p className="text-gray-600">Price: ${holding.price}</p>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <p className="text-xl font-bold text-gray-800">Total Portfolio Value: ${totalValue}</p>
      </div>

      <div className="mt-4">
        <div className="text-xl font-bold text-gray-800">Risk Score: {riskScore}</div>
        <div className="mt-2 w-full md:w-3/4">
          {/* Risk Score Visualization - Placeholder */}
          <div className="progress progress-circle bg-blue-500">
            <div className="progress-bar bg-blue-700"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioOverview;