import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, Title, Label } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { use } from 'react';

// Placeholder data - replace with actual data fetching
interface CryptoData {
  symbol: string;
  price: number;
}

interface RiskAssessmentData {
  riskLevel: string;
  potentialLoss: number;
}

type NFTPosition = {
  tokenId: string;
  quantity: number;
  price: number;
  defiProtocol: string;
};

type PortfolioData = {
  assets: CryptoData[];
  nftPositions: NFTPosition[];
};

type AppState = {
  portfolio: PortfolioData | null;
  riskAssessment: RiskAssessmentData | null;
  loading: boolean;
  theme: 'light' | 'dark';
};

const App: React.FC<AppState> = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<string>('light');

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      const fakePortfolioData: PortfolioData = {
        assets: [
          { symbol: 'BTC', price: 60000 },
          { symbol: 'ETH', price: 3000 },
        ],
        nftPositions: [
          { tokenId: 'Mossland1', quantity: 5, price: 100, defiProtocol: 'Uniswap' },
          { tokenId: 'Mossland2', quantity: 2, price: 150, defiProtocol: 'Sushi' },
        ],
      };
      const fakeRiskAssessmentData: RiskAssessmentData = {
        riskLevel: 'Medium',
        potentialLoss: 5,
      };

      setPortfolio(fakePortfolioData);
      setRiskAssessment(fakeRiskAssessmentData);
      setLoading(false);
    }, 2000);
  }, []);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const data = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'BTC Price',
        data: [60000, 65000, 62000, 63000, 61000],
        fill: false,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.4,
      },
    ],
  };

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'dark' : ''}`}>
      <header className="bg-white shadow-md p-4 flex items-center justify-between">
        <button onClick={toggleTheme} className="text-gray-500 hover:text-gray-800">
          Toggle Theme
        </button>
        <h1 className="text-xl font-bold">GPT-5 DeFi Rebalancing Agent</h1>
      </header>

      <main className="p-4">
        {loading && <p>Loading data...</p>}

        <section className="mb-4">
          <h2>Portfolio Overview</h2>
          <p>Total Portfolio Value: ${portfolio?.assets.reduce((sum, item) => sum + item.price, 0)}</p>
        </section>

        <section className="mb-4">
          <h2>Risk Assessment</h2>
          <p>Risk Level: {riskAssessment ? riskAssessment.riskLevel : 'N/A'}</p>
          <p>Potential Loss: ${riskAssessment ? riskAssessment.potentialLoss : 'N/A'}</p>
        </section>

        <section className="mb-4">
          <h2>Asset Prices</h2>
          <Line data={data} />
        </section>

        {/* Placeholder for NFT Position Details */}
        <section className="mb-4">
          <h2>NFT Position Details</h2>
          {portfolio?.nftPositions.map((pos) => (
            <div key={pos.tokenId} className="border p-3 rounded-md mb-2">
              <p>Token ID: {pos.tokenId}</p>
              <p>Quantity: {pos.quantity}</p>
              <p>Price: ${pos.price}</p>
              <p>Defi Protocol: {pos.defiProtocol}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
};

export default App;