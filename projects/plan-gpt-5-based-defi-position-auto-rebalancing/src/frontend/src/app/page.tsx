import React, { useState, useEffect } from 'react';
import { FaArrowDown, FaArrowUp } from 'react-icons/fa';
import { Chart } from 'chart.js';

// Tailwind CSS configuration (simplified for brevity)
const tailwindConfig = {
  darkMode: 'dark',
  colors: {
    'primary': '#569CD6',
    'secondary': '#FFD700',
    'accent': '#0070F3',
    'neutral': {
      '50': '#F0F4F5',
      '100': '#E1E8EB',
      '200': '#CBD5E0',
      '300': '#A0AEC0',
      '400': '#718096',
      '500': '#4E566A',
      '600': '#1F2429',
      '700': '#171923',
      '800': '#0E161B',
      '900': '#090B12',
    },
    'gray': '#9E9E9E',
  },
};

// Dummy data for demonstration
interface NFTCollateral {
  tokenId: string;
  quantity: number;
  price: number;
}

interface RiskMetrics {
  totalValue: number;
  riskScore: number;
}

const CollateralDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [nftCollateralData, setNftCollateralData] = useState<NFTCollateral[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics>({
    totalValue: 0,
    riskScore: 0,
  });

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      const dummyData: NFTCollateral[] = [
        { tokenId: 'MSL1', quantity: 10, price: 1000 },
        { tokenId: 'MSL2', quantity: 5, price: 2000 },
        { tokenId: 'MSL3', quantity: 20, price: 500 },
      ];
      setNftCollateralData(dummyData);
      setRiskMetrics({
        totalValue: dummyData.reduce((sum, item) => sum + item.quantity * item.price, 0),
        riskScore: Math.random() * 100,
      });
      setLoading(false);
    }, 1500);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-gray-100 dark:bg-gray-900 shadow-md p-4 flex items-center justify-between">
        <h1>GPT-5 DeFi Position Auto-Rebalancing</h1>
        <nav>
          <a href="#" className="text-gray-600 dark:text-gray-400">Overview</a>
          <a href="#" className="text-gray-600 dark:text-gray-400">Risk Monitoring</a>
          <a href="#" className="text-gray-600 dark:text-gray-400">Settings</a>
        </nav>
      </header>

      <main className="p-4 flex flex-row">
        <aside className="w-64 bg-gray-100 dark:bg-gray-800 p-4 border-r">
          <h2>NFT Collateral</h2>
          {nftCollateralData.map((item) => (
            <NFTCollateralCard key={item.tokenId} tokenId={item.tokenId} quantity={item.quantity} price={item.price} />
          ))}
        </aside>

        <main className="flex-grow w-full p-4">
          <h2>Risk Monitoring</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Placeholder for risk metrics chart */}
            <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-4">
              <h3>Total Value</h3>
              <p className="font-bold text-xl">{riskMetrics.totalValue.toFixed(2)}</p>
            </div>
            {/* Placeholder for risk score chart */}
            <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-4">
              <h3>Risk Score</h3>
              <p className="font-bold text-xl">{riskMetrics.riskScore.toFixed(2)}</p>
            </div>
          </div>
        </main>
      </main>
    </div>
  );
};

const NFTCollateralCard = ({ tokenId, quantity, price }: NFTCollateral) => {
  return (
    <div className="bg-gray-100 dark:bg-gray-800 rounded-md p-4 shadow-sm">
      <h3 className="font-semibold mb-2">{tokenId}</h3>
      <p className="text-gray-700 dark:text-gray-400">Quantity: {quantity}</p>
      <p className="text-gray-700 dark:text-gray-400">Price: ${price}</p>
    </div>
  );
};

export default CollateralDashboard;