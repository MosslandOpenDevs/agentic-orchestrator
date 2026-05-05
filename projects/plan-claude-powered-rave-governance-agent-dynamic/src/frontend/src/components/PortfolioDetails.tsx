import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface PortfolioDetailsProps {
  portfolioId: string;
}

const PortfolioDetails: React.FC<PortfolioDetailsProps> = ({ portfolioId }) => {
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id') || portfolioId;
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const response = await fetch(`https://api.raveportfolio.com/portfolios/${id}`); // Replace with your API endpoint
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setPortfolioData(data);
        setIsLoading(false);
        setError(null);
      } catch (error: any) {
        setIsLoading(false);
        setError(error.message);
      }
    };

    fetchPortfolioData();
  }, [id]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Loading portfolio details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Error loading portfolio details: {error}</p>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">No portfolio data found.</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex">
      <div className="md:w-3/4">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          {portfolioData.name}
        </h1>
        <p className="text-gray-700 mb-4">
          {portfolioData.description}
        </p>

        {/* Transaction History */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-800 mb-2">Transaction History</h3>
          {portfolioData.transactions &&
            portfolioData.transactions.map((transaction) => (
              <p key={transaction.id} className="text-gray-600">
                {transaction.date} - {transaction.type} - {transaction.amount}
              </p>
            ))}
        </div>

        {/* Asset Allocation */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-800 mb-2">Asset Allocation</h3>
          <p className="text-gray-700">
            {portfolioData.assetAllocation &&
              Object.entries(portfolioData.assetAllocation).map(
                ([asset, percentage]) => (
                  <p key={asset}>
                    {asset}: {percentage}%
                  </p>
                )
              )}
          </p>
        </div>

        {/* Risk Metrics */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-800 mb-2">Risk Metrics</h3>
          <p className="text-gray-700">
            Volatility: {portfolioData.riskMetrics?.volatility || 'N/A'}
            <br />
            Sharpe Ratio: {portfolioData.riskMetrics?.sharpeRatio || 'N/A'}
          </p>
        </div>
      </div>

      {/* Placeholder for visualization - Replace with actual chart component */}
      <div className="md:w-1/4">
        <p className="text-gray-600">Chart Visualization Placeholder</p>
      </div>
    </div>
  );
};

export default PortfolioDetails;