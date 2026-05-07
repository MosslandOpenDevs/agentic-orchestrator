import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart as ChartJS, Title, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';

// Dummy data for demonstration
interface CryptoData {
  id: string;
  symbol: string;
  price: number;
}

interface NFTValuation {
  tokenId: string;
  value: number;
  timestamp: string;
}

interface YieldFarmStrategy {
  riskTolerance: 'low' | 'medium' | 'high';
  strategyName: string;
}

type Portfolio = {
  nfts: NFTValuation[];
  yieldFarms: YieldFarmStrategy[];
};

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const userId = searchParams.get('userId') || 'defaultUser';

  // Dummy data for demonstration
  const cryptoData: CryptoData[] = [
    { id: 'BTC', symbol: 'BTC', price: 30000 },
    { id: 'ETH', symbol: 'ETH', price: 2000 },
  ];

  const portfolioData: Portfolio = {
    nfts: [
      { tokenId: 'NFT1', value: 100, timestamp: '2024-01-01T12:00:00Z' },
      { tokenId: 'NFT2', value: 500, timestamp: '2024-01-01T13:00:00Z' },
    ],
    yieldFarms: [
      { riskTolerance: 'medium', strategyName: 'StrategyA' },
      { riskTolerance: 'high', strategyName: 'StrategyB' },
    ],
  };

  const [loading, setLoading] = useState(true);
  const [nftValuations, setNftValuations] = useState<NFTValuation[]>([]);
  const [portfolio, setPortfolio] = useState<Portfolio>(portfolioData);

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setNftValuations(portfolio.nfts);
      setLoading(false);
    }, 1500);
  }, []);

  const data = {
    labels: nftValuations.map((v) => new Date(v.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'NFT Value',
        data: nftValuations.map((v) => v.value),
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>Mossland Strategic Advantage</h1>
        <nav>
          <ul className="flex space-x-4">
            <li>Dashboard</li>
            <li>Valuations</li>
            <li>Strategies</li>
          </ul>
        </nav>
      </header>

      <main className="mt-8 p-4">
        {loading ? (
          <div className="text-center">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* NFT Valuation Card */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">NFT Valuation</h2>
              <p className="text-gray-700">
                Estimated Cost: $250,000 - $400,000
              </p>
              <Line data={data} options={{
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
                plugins: {
                  title: {
                    display: true,
                    text: 'NFT Value Over Time'
                  },
                  legend: {
                    display: false
                  }
                }
              }} />
            </div>

            {/* Yield Farming Configuration Card */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">Yield Farming</h2>
              <p className="text-gray-700">
                Configure your risk tolerance and yield farming strategies.
              </p>
              {/* Add more UI elements here */}
            </div>

            {/* User Portfolio Overview Card */}
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-lg font-bold mb-4">Portfolio Overview</h2>
              <p className="text-gray-700">
                {portfolio.nfts.length} NFTs, {portfolio.yieldFarms.length} Yield Farms
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;