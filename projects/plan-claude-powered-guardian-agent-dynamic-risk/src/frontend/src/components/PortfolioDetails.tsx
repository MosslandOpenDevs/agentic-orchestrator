import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface PortfolioDetailsProps {
  portfolioId: string;
}

const PortfolioDetails: React.FC<PortfolioDetailsProps> = ({ portfolioId }) => {
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/portfolio/${portfolioId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setPortfolioData(data);
        setLoading(false);
        setError(null);
      } catch (error: any) {
        setError(error.message);
        setLoading(false);
      }
    };

    fetchData();
  }, [portfolioId]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading portfolio details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Error loading portfolio details: {error}</p>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>No portfolio data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex">
      <div className="w-full">
        <h2 className="text-xl font-bold mb-4">{portfolioData.name}</h2>
        <p className="text-gray-700 mb-4">
          <strong>Total Value:</strong> ${portfolioData.totalValue}
        </p>

        {/* Asset Breakdown */}
        <div className="mb-4">
          <h3 className="text-lg font-bold mb-2">Asset Breakdown</h3>
          <ul className="list-disc pl-5 mb-4">
            {portfolioData.assets.map((asset) => (
              <li key={asset.name} className="mb-1">
                {asset.name}: {asset.percentage}%
              </li>
            ))}
          </ul>
        </div>

        {/* Performance Metrics */}
        <div className="mb-4">
          <h3 className="text-lg font-bold mb-2">Performance Metrics</h3>
          <p className="text-gray-700 mb-2">
            <strong>Return:</strong> {portfolioData.return}%
          </p>
          <p className="text-gray-700 mb-2">
            <strong>Volatility:</strong> {portfolioData.volatility}%
          </p>
        </div>

        {/* Rebalancing History */}
        <div className="mb-4">
          <h3 className="text-lg font-bold mb-2">Rebalancing History</h3>
          <table className="table-auto border">
            <thead>
              <tr className="text-left">
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Change</th>
                <th className="px-4 py-2">New Percentage</th>
              </tr>
            </thead>
            <tbody>
              {portfolioData.rebalancingHistory.map((rebalance) => (
                <tr key={rebalance.date} className="text-left">
                  <td className="px-4 py-2">{rebalance.date}</td>
                  <td className="px-4 py-2">{rebalance.change}%</td>
                  <td className="px-4 py-2">{rebalance.newPercentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PortfolioDetails;