import React, { useState, useEffect } from 'react';
import { useViewport } from 'react-use';

interface PortfolioItem {
  id: string;
  name: string;
  assetType: string;
  quantity: number;
  currentPrice: number;
  totalValue: number;
}

interface PortfolioDashboardProps {
  data: PortfolioItem[];
  isLoading: boolean;
  error?: string;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ data, isLoading, error }) => {
  const { width } = useViewport();
  const [isMobile, setIsMobile] = useState(width < 768);

  useEffect(() => {
    setIsMobile(width < 768);
  }, [width]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md text-red-700">
        <p>Error loading portfolio data: {error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>No portfolio data available.</p>
      </div>
    );
  }

  return (
    <div className={`bg-white p-4 rounded-lg shadow-md flex ${isMobile ? 'flex-col' : 'flex-row'}  max-w-screen-xl  mx-auto`}>
      {/* Left Side - Portfolio Visualization */}
      <div className={`w-full ${isMobile ? 'mb-4' : 'mr-4'} rounded-lg shadow-md`}>
        <h2 className="text-xl font-semibold mb-4">Portfolio Overview</h2>
        {data.map((item) => (
          <div
            key={item.id}
            className={`bg-gray-100 p-4 rounded-md hover:bg-gray-200 flex items-center justify-between border-l-4 border-gray-300`}
            aria-label={item.name}
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && console.log('Item pressed')}
          >
            <p className="font-semibold">{item.name}</p>
            <p className="text-gray-600">{item.assetType} - {item.quantity}</p>
            <p className="text-lg font-bold">${item.totalValue.toFixed(2)}</p>
          </div>
        ))}
      </div>

      {/* Right Side - Asset Details */}
      <div className={`w-full ${isMobile ? 'mb-4' : 'mr-4'} rounded-lg shadow-md`}>
        <h2 className="text-xl font-semibold mb-4">Asset Details</h2>
        {data.length > 0 && (
          <div className="p-4">
            <p>Total Portfolio Value: ${data.reduce((sum, item) => sum + item.totalValue, 0).toFixed(2)}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioDashboard;