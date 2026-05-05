import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface SecurityToken {
  symbol: string;
  name: string;
  description: string;
  currentPrice: number;
}

interface PositionHistoryItem {
  date: string;
  quantity: number;
  price: number;
}

interface PortfolioDetailProps {
  securityToken: SecurityToken;
  positionHistory: PositionHistoryItem[];
}

const PortfolioDetail: React.FC<PortfolioDetailProps> = ({ securityToken, positionHistory }) => {
  const [searchParams] = useSearchParams();
  const portfolioId = searchParams.get('portfolioId');
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
        <div className="text-xl font-bold text-gray-800">Loading Portfolio Details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-gray-800">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex flex-row max-w-4xl">
      <div className="flex-1">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">{securityToken.name}</h2>
        <p className="text-gray-700 mb-4">Symbol: {securityToken.symbol}</p>
        <p className="text-gray-700 mb-4">{securityToken.description}</p>
        <p className="text-xl font-bold text-green-600 mb-4">Current Price: ${securityToken.currentPrice.toFixed(2)}</p>
      </div>

      <div className="flex-1">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Position History</h3>
        {positionHistory.length > 0 ? (
          <table>
            <thead>
              <tr className="text-white bg-gray-800">
                <th>Date</th>
                <th>Quantity</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {positionHistory.map((item) => (
                <tr key={item.date} className="text-gray-700">
                  <td>{item.date}</td>
                  <td>{item.quantity}</td>
                  <td>${item.price.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-700">No position history available.</p>
        )}
      </div>

      <div className="flex-1">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Performance Charts</h3>
        {/* Placeholder for performance charts - Replace with actual charting library */}
        <p className="text-gray-700">Performance charts will be displayed here.</p>
      </div>
    </div>
  );
};

export default PortfolioDetail;