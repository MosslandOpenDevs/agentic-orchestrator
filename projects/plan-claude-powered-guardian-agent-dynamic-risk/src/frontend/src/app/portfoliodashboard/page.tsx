import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useWindowSize } from '@react-use/windowsize';

interface PortfolioData {
  assets: {
    [asset: string]: {
      name: string;
      value: number;
      allocation: number;
    };
  };
  riskProfile: string;
}

interface PortfolioDashboardProps {
  initialData?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialData }) => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { width } = useWindowSize();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: PortfolioData = {
          assets: {
            'Stocks': { name: 'Stocks', value: 10000, allocation: 50 },
            'Bonds': { name: 'Bonds', value: 5000, allocation: 30 },
            'Crypto': { name: 'Crypto', value: 2000, allocation: 20 },
          },
          riskProfile: 'Moderate',
        };
        setPortfolioData(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

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

  const handleRebalance = () => {
    router.push('/rebalance');
  };

  return (
    <div className={`container mx-auto px-4 py-8 ${width > 768 ? 'md:px-16' : 'sm:px-4'}`}>
      <h1 className="text-3xl font-bold mb-4 text-center">Portfolio Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {Object.entries(portfolioData.assets).map(([assetName, assetInfo]) => (
          <div
            key={assetName}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300"
            aria-label={`Portfolio asset: ${assetInfo.name}`}
          >
            <h2 className="text-xl font-semibold mb-2">{assetInfo.name}</h2>
            <p className="text-gray-700">Value: ${assetInfo.value}</p>
            <p className="text-gray-700">Allocation: {assetInfo.allocation}%</p>
          </div>
        ))}
      </div>

      <button
        onClick={handleRebalance}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4 w-full max-w-md"
        aria-label="Rebalance Portfolio"
      >
        Rebalance Portfolio
      </button>
    </div>
  );
};

export default PortfolioDashboard;