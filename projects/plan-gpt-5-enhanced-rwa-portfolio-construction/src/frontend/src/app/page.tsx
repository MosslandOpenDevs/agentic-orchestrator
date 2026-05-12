import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart as ChartJS, Title, Label } from 'chart.js';
import { Line } from 'react-chartjs-2';

// Dummy data for demonstration
interface RWAAsset {
  id: string;
  name: string;
  price: number;
}

interface Portfolio {
  assets: RWAAsset[];
  totalValue: number;
}

type RiskTolerance = 'low' | 'medium' | 'high';

type GPT5Recommendation = {
  asset: RWAAsset;
  action: 'buy' | 'sell' | 'hold';
  quantity: number;
};

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const riskToleranceParam = searchParams.get('riskTolerance') || 'medium';
  const [portfolio, setPortfolio] = useState<Portfolio>({
    assets: [],
    totalValue: 0,
  });
  const [gpt5Recommendations, setGpt5Recommendations] = useState<GPT5Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      const assets: RWAAsset[] = [
        { id: 'asset1', name: 'BTC', price: 30000 },
        { id: 'asset2', name: 'ETH', price: 1800 },
        { id: 'asset3', name: 'USDC', price: 1 },
      ];
      setPortfolio({ assets, totalValue: assets.reduce((acc, asset) => acc + asset.price, 0) });
      setGpt5Recommendations([
        { asset: assets[0], action: 'buy', quantity: 10 },
        { asset: assets[1], action: 'sell', quantity: 5 },
      ]);
      setIsLoading(false);
    }, 2000);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const data = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Portfolio Value',
        data: [1000, 1200, 1500, 1300, 1600],
        fill: true,
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className={`min-h-screen ${theme}`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <span onClick={toggleTheme} className="text-blue-500">
          {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
        </span>
      </header>

      <main className="p-4 flex">
        <aside className="w-64 bg-gray-200 p-4">
          {/* Sidebar content */}
          <h2 className="text-lg font-semibold mb-4">Risk Tolerance</h2>
          <button
            onClick={() => setRiskToleranceParam('low')}
            className="bg-blue-500 text-white px-4 py-2 rounded-md"
          >
            Low
          </button>
          <button
            onClick={() => setRiskToleranceParam('medium')}
            className="bg-indigo-500 text-white px-4 py-2 rounded-md"
          >
            Medium
          </button>
          <button
            onClick={() => setRiskToleranceParam('high')}
            className="bg-red-500 text-white px-4 py-2 rounded-md"
          >
            High
          </button>
        </aside>

        <section className="w-full">
          {isLoading ? (
            <div className="text-center p-4">Loading portfolio data...</div>
          ) : (
            <>
              <h1 className="text-2xl font-bold mb-4">TerraForm Dashboard</h1>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Portfolio Overview */}
                <div className="bg-white p-4 rounded-md shadow-md">
                  <h3 className="text-lg font-semibold mb-2">Portfolio Summary</h3>
                  <p className="text-gray-700">Total Value: ${portfolio.totalValue.toFixed(2)}</p>
                </div>

                {/* RWA Asset Details */}
                <div className="bg-white p-4 rounded-md shadow-md">
                  <h3 className="text-lg font-semibold mb-2">Asset Details</h3>
                  {portfolio.assets.map((asset) => (
                    <div key={asset.id} className="flex items-center mb-2">
                      <span className="text-lg font-semibold">{asset.name}</span>
                      <span className="text-gray-700 ml-2">${asset.price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                {/* Rebalancing Recommendations */}
                <div className="bg-white p-4 rounded-md shadow-md">
                  <h3 className="text-lg font-semibold mb-2">Rebalancing Recommendations</h3>
                  {gpt5Recommendations.map((recommendation) => (
                    <div key={recommendation.asset.id} className="flex items-center mb-2">
                      <span className="text-lg font-semibold">{recommendation.asset.name}</span>
                      <p className="text-gray-700 ml-2">
                        {recommendation.action === 'buy' ? 'Buy' : recommendation.action === 'sell' ? 'Sell' : 'Hold'} {recommendation.quantity}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Chart Placeholder */}
              <div className="bg-white p-4 rounded-md shadow-md mt-4">
                <h3 className="text-lg font-semibold mb-2">Portfolio Performance</h3>
                <ChartJS
                  type="line"
                  data={data}
                  options={{
                    scales: {
                      y: {
                        beginAtZero: true,
                      },
                    },
                  }}
                />
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;