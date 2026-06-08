import React, { useState, useEffect } from 'react';
import { useDarkMode } from './useDarkMode'; // Assuming this hook exists
import { CoinGeckoData } from './types'; // Assuming this type exists
import { fetchData } from './api'; // Assuming this function exists

// Dummy data for demonstration
const initialPortfolioData: any = {
  portfolioId: '1',
  assets: [
    { assetId: '1', name: 'ETH', quantity: 10, price: 3000 },
    { assetId: '2', name: 'BTC', quantity: 5, price: 60000 },
  ],
};

const Dashboard: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<any>(initialPortfolioData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [coinGeckoData, setCoinGeckoData] = useState<CoinGeckoData[] | null>(null);
  const isDarkMode = useDarkMode();

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const data = await fetchData('portfolioData');
        setPortfolioData(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        setLoading(false);
      }
    };

    const fetchCoinGecko = async () => {
      try {
        const data = await fetchData('coinGeckoData');
        setCoinGeckoData(data);
      } catch (err) {
        setError('Failed to load coinGecko data.');
        setLoading(false);
      }
    };

    fetchPortfolio();
    fetchCoinGecko();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const styles = isDarkMode ? 'bg-gray-800 text-gray-100' : 'bg-white text-gray-800';

  return (
    <div className={`${styles} min-h-screen flex`}>
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>GPT-5 DeFi Rebalancer</h1>
        <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Dark Mode
        </button>
      </header>

      <aside className="bg-gray-800 text-white p-4">
        {/* Sidebar content */}
        <h2>Portfolio Overview</h2>
        <p>Total Portfolio Value: {portfolioData.assets.reduce((sum, asset) => sum + asset.quantity * asset.price, 0)}</p>
      </aside>

      <main className="p-4 flex">
        {/* Portfolio Details */}
        <PortfolioDetails portfolioData={portfolioData} />

        {/* Asset Cards */}
        <div className="ml-4">
          {portfolioData.assets.map((asset) => (
            <AssetCard key={asset.assetId} asset={asset} coinGeckoData={coinGeckoData} />
          ))}
        </div>
      </main>
    </div>
  );
};

interface PortfolioDetailsProps {
  portfolioData: any;
}

const PortfolioDetails: React.FC<PortfolioDetailsProps> = ({ portfolioData }) => {
  return (
    <div className="w-1/2 p-4 border rounded-lg shadow-md">
      <h2>Portfolio Details</h2>
      <p>Portfolio ID: {portfolioData.portfolioId}</p>
    </div>
  );
};

interface AssetCardProps {
  asset: any;
  coinGeckoData?: CoinGeckoData[];
}

const AssetCard: React.FC<AssetCardProps> = ({ asset, coinGeckoData }) => {
  const price = coinGeckoData ? coinGeckoData.find(c => c.id === asset.name)?.current_price : null;

  return (
    <div className="w-1/2 p-4 border rounded-lg shadow-md">
      <h3>{asset.name}</h3>
      <p>Quantity: {asset.quantity}</p>
      {price ? <p>Price: ${price}</p> : <p>Price: Loading...</p>}
    </div>
  );
};

export default Dashboard;