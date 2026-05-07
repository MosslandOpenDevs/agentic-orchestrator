import React, { useState, useEffect } from 'react';
import { FaArrowDown, FaArrowUp } from 'react-icons/fa';
import { Chart as ChartJS, Title, Label, LineElement, CategoryScale } from 'chart.js';
import { Line } from 'react-chartjs-2';

// Placeholder data - replace with actual data fetching
const initialPortfolioData = {
  nftPositions: [
    { tokenId: 'NFT1', name: 'NFT A', quantity: 10, price: 100, change: 0.05 },
    { tokenId: 'NFT2', name: 'NFT B', quantity: 5, price: 200, change: -0.02 },
  ],
};

type NFTPosition = {
  tokenId: string;
  name: string;
  quantity: number;
  price: number;
  change: number;
};

type PortfolioData = {
  nftPositions: NFTPosition[];
};

const Dashboard = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData>(initialPortfolioData);
  const [loading, setLoading] = useState<boolean>(true);
  const [riskProfile, setRiskProfile] = useState<string>('Moderate');
  const [theme, setTheme] = useState<string>('light');

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setPortfolioData(initialPortfolioData);
      setLoading(false);
    }, 1500);
  }, []);

  const handleRiskProfileChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setRiskProfile(event.target.value);
  };

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const dataForChart = {
    labels: portfolioData.nftPositions.map((pos) => 'Time'),
    datasets: [
      {
        label: 'Price Change',
        data: portfolioData.nftPositions.map((pos) => pos.change),
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className={`min-h-screen ${theme === 'light' ? 'bg-white' : 'bg-gray-100'} flex flex-col`}>
      <header className={`bg-gray-800 text-white py-4 px-6 flex items-center justify-between`}>
        <span onClick={toggleTheme} className="text-blue-500 cursor-pointer">
          {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
        </span>
        <h1 className="text-2xl font-bold">GPT-5 Powered Liquidity Agent</h1>
      </header>

      <main className={`flex-grow px-6 py-4`}>
        <aside className={`bg-gray-800 text-white p-4 w-64`}>
          <h2 className="text-lg font-semibold mb-4">Risk Profile</h2>
          <select
            className="bg-gray-200 p-2 rounded border border-gray-300"
            value={riskProfile}
            onChange={handleRiskProfileChange}
          >
            <option value="Conservative">Conservative</option>
            <option value="Moderate">Moderate</option>
            <option value="Aggressive">Aggressive</option>
          </select>
        </aside>

        <div className="flex-grow w-full ml-4">
          {loading ? (
            <div className="text-center p-4">Loading...</div>
          ) : (
            <>
              <section className="mb-4">
                <h2 className="text-xl font-bold mb-2">Portfolio Overview</h2>
                {portfolioData.nftPositions.map((position) => (
                  <NFTPositionCard
                    key={position.tokenId}
                    tokenId={position.tokenId}
                    name={position.name}
                    quantity={position.quantity}
                    price={position.price}
                    change={position.change}
                  />
                ))}
              </section>

              <section className="mb-4">
                <h2 className="text-xl font-bold mb-2">Price Chart</h2>
                <Line data={dataForChart} options={{
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: {
                        display: true,
                        text: 'Price Change'
                      }
                    },
                    x: {
                      title: {
                        display: true,
                        text: 'Time'
                      }
                    }
                  }
                }}/>
              </section>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

const NFTPositionCard = ({
  tokenId,
  name,
  quantity,
  price,
  change,
}): { tokenId: string; name: string; quantity: number; price: number; change: number } => (
  <div className="bg-gray-100 p-4 rounded shadow-md mb-2">
    <h3 className="text-lg font-semibold mb-2">{name}</h3>
    <p className="text-gray-700">Quantity: {quantity}</p>
    <p className="text-gray-700">Price: ${price}</p>
    <p className="text-gray-700">Change: {(change > 0 ? <FaArrowUp className="text-green-500" /> : <FaArrowDown className="text-red-500" />)} {Math.abs(change).toFixed(2)}</p>
  </div>
);

export default Dashboard;