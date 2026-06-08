import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import {
  Chart as ChartJs,
  LineElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Placeholder data - Replace with actual data fetching
interface PortfolioData {
  assets: {
    name: string;
    quantity: number;
    price: number;
  }[];
}

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const userId = searchParams.get('userId') || 'defaultUser';
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Simulate fetching data
    const fetchData = async () => {
      try {
        // Replace with actual API calls
        const data = {
          assets: [
            { name: 'Mossland NFT A', quantity: 10, price: 150 },
            { name: 'ETH', quantity: 100, price: 3000 },
            { name: 'USDC', quantity: 1000, price: 1 },
          ],
        };
        setPortfolioData(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleDarkModeToggle = () => {
    setDarkMode(!darkMode);
  };

  const options = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Portfolio Performance',
      },
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Price',
        },
      },
    },
  };

  const chartData = {
    labels: [],
    datasets: [
      {
        label: 'Price',
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  useEffect(() => {
    if (portfolioData) {
      chartData.labels = Array.from({ length: 10 }, (_, i) => i);
      chartData.datasets[0].data = portfolioData.assets.map(asset => asset.price);
    }
  }, [portfolioData]);

  return (
    <div className={`min-h-screen dark-mode-${darkMode}`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <h1>Mossland AI Portfolio</h1>
        <button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={handleDarkModeToggle}>
          Dark Mode
        </button>
      </header>

      <main className="p-4 flex">
        <aside className="w-64 bg-gray-200 p-4">
          <h2>Risk Profile</h2>
          <button>Conservative</button>
          <button>Moderate</button>
          <button>Aggressive</button>
        </aside>

        <main className="flex-grow">
          {loading && <p>Loading portfolio data...</p>}
          {portfolioData && (
            <div>
              <h2>Portfolio Overview</h2>
              <p>User ID: {userId}</p>
              <h3>Assets</h3>
              {portfolioData.assets.map(asset => (
                <div key={asset.name} className="mb-4 p-4 border rounded shadow-md">
                  <p>{asset.name}</p>
                  <p>Quantity: {asset.quantity}</p>
                  <p>Price: ${asset.price}</p>
                </div>
              ))}
              <Bar data={chartData} options={options} />
            </div>
          )}
        </main>
      </main>
    </div>
  );
};

export default Dashboard;