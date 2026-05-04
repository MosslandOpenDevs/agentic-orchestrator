import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { use } from 'react';

// Placeholder data - Replace with actual data fetching
interface PortfolioData {
  name: string;
  assets: {
    tokenId: string;
    quantity: number;
    price: number;
  }[];
}

interface MarketData {
  tokenId: string;
  price: number;
  volume: number;
}

type ChartData = {
  labels: string[];
  data: number[];
};

const Dashboard: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [marketData, setMarketData] = useState<MarketData[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<string>("light");

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      const fakePortfolio: PortfolioData = {
        name: "My Mossland Portfolio",
        assets: [
          { tokenId: "0x123", quantity: 10, price: 100 },
          { tokenId: "0x456", quantity: 5, price: 200 },
        ],
      };
      setPortfolioData(fakePortfolio);
      setTimeout(() => {
        const fakeMarketData: MarketData[] = [
          { tokenId: "0x123", price: 105, volume: 100 },
          { tokenId: "0x456", price: 210, volume: 50 },
        ];
        setMarketData(fakeMarketData);
        setLoading(false);
      }, 1500);
    }, 1000);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const data: ChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    data: [10, 15, 13, 17, 20],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div className={`min-h-screen ${theme === 'light' ? 'bg-white' : 'bg-gray-100'} flex flex-col ${theme === 'light' ? 'text-gray-800' : 'text-gray-50'}  `}>
      <header className="bg-gray-50 shadow-md p-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Mossland Portfolio Dashboard</h1>
        <button onClick={toggleTheme} className="bg-gray-300 p-2 rounded-md">
          {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
        </button>
      </header>

      <main className="flex-grow p-4">
        {loading ? (
          <div className="text-center mt-8">Loading data...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Portfolio Overview */}
            <div className="bg-white rounded-md shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">Portfolio Summary</h2>
              {portfolioData && (
                <>
                  <p>Portfolio Name: {portfolioData.name}</p>
                  {portfolioData.assets.map((asset) => (
                    <div key={asset.tokenId} className="mb-2">
                      {asset.tokenId} - {asset.quantity} - ${asset.price}
                    </div>
                  ))}
                </>
              )}
            </div>

            {/* Market Data Chart */}
            <div className="bg-white rounded-md shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">Asset Prices</h2>
              <Line data={data} options={chartOptions} className="mt-4" />
            </div>

            {/* Placeholder for other widgets */}
            <div className="bg-white rounded-md shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">Other Metrics</h2>
              {/* Add more widgets here */}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;