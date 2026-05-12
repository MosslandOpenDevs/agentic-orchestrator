import React, { useState, useEffect } from 'react';
import { useNextRouter } from 'next/router';

interface PortfolioItem {
  asset: string;
  quantity: number;
  price: number;
}

interface PortfolioOverviewProps {
  assets: PortfolioItem[];
}

const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ assets }) => {
  const router = useNextRouter();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    const fetchData = async () => {
      try {
        // Mock data for demonstration
        const mockAssets = assets.map(asset => ({
          asset: asset.asset,
          quantity: Math.floor(Math.random() * 100),
          price: Math.floor(Math.random() * 1000)
        }));

        setLoading(false);
        // Replace this with your actual data fetching logic
        // Example:
        // const response = await fetch('/api/portfolio');
        // const data = await response.json();
        // setData(data);

      } catch (err) {
        setError('Failed to load portfolio data.');
        console.error('Error fetching portfolio data:', err);
      }
    };

    fetchData();
  }, [assets]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-xl font-bold">Loading Portfolio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-xl font-bold text-red-700">Error: {error}</p>
      </div>
    );
  }

  const totalValue = assets.reduce((sum, asset) => sum + asset.quantity * asset.price, 0);

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
      <h2 className="text-2xl font-bold mb-4">Portfolio Overview</h2>

      <div className="w-full md:w-3/4 flex flex-col mb-4">
        {assets.map((asset) => (
          <div
            key={asset.asset}
            className="bg-white p-4 rounded-md shadow-sm mb-2 hover:shadow-lg transition duration-300"
            aria-label={`Details for ${asset.asset}`}
          >
            <p className="text-lg font-semibold mb-2">{asset.asset}</p>
            <p className="text-base font-normal">Quantity: {asset.quantity}</p>
            <p className="text-base font-normal">Price: ${asset.price}</p>
          </div>
        ))}
      </div>

      <div className="w-full md:w-3/4">
        <p className="text-xl font-semibold mb-2">Total Portfolio Value: ${totalValue}</p>
      </div>

      <div className="w-full md:w-3/4">
        <button
          onClick={() => router.push('/rebalance')}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full md:w-2/3"
          aria-label="Rebalance Portfolio"
        >
          Rebalance Portfolio
        </button>
      </div>
    </div>
  );
};

export default PortfolioOverview;