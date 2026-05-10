import React, { useState, useEffect } from 'react';
import { useServerApi } from '../../utils/serverApi'; // Assuming serverApi is defined elsewhere
import { NFTPortfolioItem } from '../../types/NFTPortfolioItem';

interface PortfolioDashboardProps {
  userId: string;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ userId }) => {
  const [portfolioData, setPortfolioData] = useState<NFTPortfolioItem[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { getPortfolio } = useServerApi();

  useEffect(() => {
    const fetchPortfolio = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getPortfolio(userId);
        if (data) {
          setPortfolioData(data);
        } else {
          setError('Failed to retrieve portfolio data.');
        }
      } catch (err: any) {
        setError(err.message || 'An error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolio();
  }, [userId, getPortfolio]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Loading portfolio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Error: {error}</p>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">No portfolio data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col">
      <h2 className="text-2xl font-bold mb-4">NFT Portfolio</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {portfolioData.map((item) => (
          <div
            key={item.tokenId}
            className="bg-white rounded-lg shadow-sm p-4 hover:shadow-lg transition duration-300"
            aria-label={`NFT: ${item.name}`}
          >
            <img
              src={item.imageUrl}
              alt={item.name}
              className="w-full h-32 object-cover rounded-lg mb-2"
            />
            <h3 className="text-lg font-semibold mb-2">{item.name}</h3>
            <p className="text-gray-700">Token ID: {item.tokenId}</p>
            <p className="text-gray-700">Quantity: {item.quantity}</p>
            <p className="text-gray-700">Current Value: ${item.currentValue.toFixed(2)}</p>
          </div>
        ))}
      </div>

      {/* Rebalancing Controls (Placeholder) */}
      <div className="mt-4 p-4 rounded-lg bg-gray-200">
        <p className="text-gray-700 mb-2">Rebalancing Controls (Placeholder)</p>
        <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full mt-2">
          Adjust Portfolio
        </button>
      </div>

      {/* NFT Value Predictions (Placeholder) */}
      <div className="mt-4 p-4 rounded-lg bg-gray-200">
        <p className="text-gray-700 mb-2">NFT Value Predictions (Placeholder)</p>
        <p className="text-gray-700">
          This section will display predicted NFT values based on market trends.
        </p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;