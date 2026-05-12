import React, { useState, useEffect } from 'react';
import { LineChart, PieChart, BarChart } from 'react-div-chart';
import { useMediaQuery } from 'react-use';

interface PortfolioData {
  totalValue: number;
  assetAllocation: {
    [key: string]: number;
  };
  rebalancingRecommendations: string[];
}

interface PortfolioDashboardProps {
  data?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ data }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const isMobile = useMediaQuery('(max-width: 768px)');

  useEffect(() => {
    if (!data) {
      setLoading(false);
      setError('No portfolio data available.');
      return;
    }

    setLoading(false);
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  const totalValue = data.totalValue;
  const assetAllocation = data.assetAllocation;
  const rebalancingRecommendations = data.rebalancingRecommendations;

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Portfolio Performance</h2>

      <div className="mb-4">
        <p className="text-xl font-semibold">Total Portfolio Value: ${totalValue}</p>
      </div>

      <div className="mb-4">
        <p className="text-xl font-semibold">Asset Allocation:</p>
        <div className="flex flex-col md:flex-row">
          {Object.entries(assetAllocation).map(([asset, percentage]) => (
            <div key={asset} className="mr-2 mb-2 md:mr-4 md:mb-0">
              <span className="text-sm font-medium">{asset}</span>
              <span className="text-sm font-medium">{percentage}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-4">
        {isMobile ? (
          <BarChart
            data={[
              { x: 'Equity', y: 40 },
              { x: 'Fixed Income', y: 30 },
              { x: 'Alternative Assets', y: 30 },
            ]}
          />
        ) : (
          <PieChart
            data={[
              { label: 'Equity', value: 40 },
              { label: 'Fixed Income', value: 30 },
              { label: 'Alternative Assets', value: 30 },
            ]}
          />
        )}
      </div>

      <div className="mb-4">
        <p className="text-xl font-semibold">Rebalancing Recommendations:</p>
        <ul className="list-disc pl-4">
          {rebalancingRecommendations.map((recommendation, index) => (
            <li key={index} className="text-sm">{recommendation}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default PortfolioDashboard;