import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart } from 'chart.js';

interface PortfolioData {
  totalValue: number;
  assets: {
    stocks: {
      name: string;
      quantity: number;
      price: number;
    }[];
    bonds: {
      name: string;
      quantity: number;
      price: number;
    }[];
    crypto: {
      name: string;
      quantity: number;
      price: number;
    }[];
    cash: {
      quantity: number;
      price: number;
    };
  };
  riskProfile: 'conservative' | 'moderate' | 'aggressive';
}

interface PortfolioDashboardProps {
  initialData?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialData }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const riskProfileParam = searchParams.get('riskProfile');
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const riskProfile = riskProfileParam || 'moderate';
        const data: PortfolioData = {
          totalValue: 100000,
          assets: {
            stocks: [
              { name: 'Apple', quantity: 10, price: 150 },
              { name: 'Microsoft', quantity: 5, price: 250 },
            ],
            bonds: [{ name: 'US Treasury', quantity: 2, price: 100 }],
            crypto: [{ name: 'Bitcoin', quantity: 1, price: 30000 }],
            cash: { quantity: 5000, price: 1 },
          },
          riskProfile: riskProfile,
        };
        setPortfolioData(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [riskProfileParam]);

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  const assetAllocationChartData = {
    labels: ['Stocks', 'Bonds', 'Crypto', 'Cash'],
    datasets: [
      {
        label: 'Allocation',
        data: [
          portfolioData.assets.stocks.reduce((a, b) => a + b.quantity * b.price, 0) / portfolioData.totalValue * 100,
          portfolioData.assets.bonds.reduce((a, b) => a + b.quantity * b.price, 0) / portfolioData.totalValue * 100,
          portfolioData.assets.crypto.reduce((a, b) => a + b.quantity * b.price, 0) / portfolioData.totalValue * 100,
          portfolioData.assets.cash.quantity / portfolioData.totalValue * 100,
        ],
        backgroundColor: ['#FF6384', '#36A6DB', '#FFDC4D', '#42a5f5'],
      },
    ],
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      <div className="flex flex-col md:flex-row mb-4">
        <div className="w-full md:w-1/2 p-4">
          <p className="text-gray-700 mb-2">Total Portfolio Value: ${portfolioData.totalValue.toFixed(2)}</p>
          <p className="text-gray-700 mb-2">Risk Profile: {portfolioData.riskProfile}</p>
        </div>
        <div className="w-full md:w-1/2 p-4">
          <canvas
            id="assetAllocationChart"
            width="400"
            height="200"
            className="mt-4"
          >
            <Chart data={assetAllocationChartData} type="pie" />
          </canvas>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-gray-700 mb-2">Asset Allocation (Percentage)</p>
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left">
              <th className="px-4 py-2 bg-gray-100">Asset</th>
              <th className="px-4 py-2 bg-gray-100">Quantity</th>
              <th className="px-4 py-2 bg-gray-100">Value</th>
              <th className="px-4 py-2 bg-gray-100">Percentage</th>
            </tr>
          </thead>
          <tbody>
            {portfolioData.assets.stocks.map((asset, index) => (
              <tr key={index} className="text-left">
                <td className="px-4 py-2">{asset.name}</td>
                <td className="px-4 py-2">{asset.quantity}</td>
                <td className="px-4 py-2">${(asset.quantity * asset.price).toFixed(2)}</td>
                <td className="px-4 py-2">{(asset.quantity * asset.price) / portfolioData.totalValue * 100}</td>
              </tr>
            ))}
            {portfolioData.assets.bonds.map((asset, index) => (
              <tr key={index} className="text-left">
                <td className="px-4 py-2">{asset.name}</td>
                <td className="px-4 py-2">{asset.quantity}</td>
                <td className="px-4 py-2">${(asset.quantity * asset.price).toFixed(2)}</td>
                <td className="px-4 py-2">{(asset.quantity * asset.price) / portfolioData.totalValue * 100}</td>
              </tr>
            ))}
            {portfolioData.assets.crypto.map((asset, index) => (
              <tr key={index} className="text-left">
                <td className="px-4 py-2">{asset.name}</td>
                <td className="px-4 py-2">{asset.quantity}</td>
                <td className="px-4 py-2">${(asset.quantity * asset.price).toFixed(2)}</td>
                <td className="px-4 py-2">{(asset.quantity * asset.price) / portfolioData.totalValue * 100}</td>
              </tr>
            ))}
            {portfolioData.assets.cash.map((asset, index) => (
              <tr key={index} className="text-left">
                <td className="px-4 py-2">Cash</td>
                <td className="px-4 py-2">{asset.quantity}</td>
                <td className="px-4 py-2">${(asset.quantity * asset.price).toFixed(2)}</td>
                <td className="px-4 py-2">{(asset.quantity * asset.price) / portfolioData.totalValue * 100}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioDashboard;