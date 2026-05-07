import React, { useState, useEffect } from 'react';
import { FaEthereum } from 'react-icons/fa';
import { FaArrowDown } from 'react-icons/fa';
import { FaArrowUp } from 'react-icons/fa';
import { FaQuestionCircle } from 'react-icons/fa';
import { FaTimesCircle } from 'react-icons/fa';

// Tailwind CSS configuration (simplified for brevity)
const tailwindConfig = {
  colors: {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'light': '#f8f9fa',
    'dark': '#343a40',
    'white': '#ffffff',
    'black': '#000000',
  },
  spacing: {
    '4': '1rem',
    '8': '2rem',
    '16': '4rem',
  },
};

// Mock Data (Replace with actual data fetching)
interface PortfolioItem {
  tokenId: string;
  name: string;
  nftType: string;
  quantity: number;
  price: number;
}

const mockPortfolioData: PortfolioItem[] = [
  { tokenId: 'NFT1', name: 'NFT A', nftType: 'ERC-721', quantity: 10, price: 1500 },
  { tokenId: 'NFT2', name: 'NFT B', nftType: 'ERC-721', quantity: 5, price: 2800 },
  { tokenId: 'NFT3', name: 'NFT C', nftType: 'ERC-721', quantity: 20, price: 800 },
];

const EstimatedCost = () => {
  return (
    <div className={`${tailwindConfig.spacing['8']} flex items-center justify-around`}>
      <div>
        <p className="text-xl font-semibold text-gray-700">Development</p>
        <p className="text-gray-400">
          $80,000 - $120,000 (depending on team size and resource allocation)
        </p>
      </div>
      <div>
        <p className="text-xl font-semibold text-gray-700">Infrastructure</p>
        <p className="text-gray-400">
          $5,000 - $10,000 (annual)
        </p>
      </div>
      <div>
        <p className="text-xl font-semibold text-gray-700">Legal & Compliance</p>
        <p className="text-gray-400">
          $10,000 - $20,000 (initial)
        </p>
      </div>
    </div>
  );
};

const PortfolioDashboard = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>(mockPortfolioData);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Simulate data fetching
    setTimeout(() => {
      setLoading(false);
    }, 1500);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-2xl font-bold text-gray-700">Loading...</p>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen flex">
      <div className="flex flex-shrink-0 w-64 bg-gray-100 h-screen">
        {/* Sidebar */}
        <div className="p-4">
          <h5 className="text-lg font-semibold text-gray-700">Portfolio</h5>
          <div className="mt-4">
            <button className="flex items-center rounded-md py-2 px-4 hover:bg-gray-200">
              <FaEthereum className="mr-2" /> Portfolio Overview
            </button>
            <button className="flex items-center rounded-md py-2 px-4 hover:bg-gray-200">
              <FaQuestionCircle className="mr-2" /> NFT Details
            </button>
            <button className="flex items-center rounded-md py-2 px-4 hover:bg-gray-200">
              <FaTimesCircle className="mr-2" /> Risk Profile Selector
            </button>
          </div>
        </div>
      </div>

      <main className="flex-grow p-4">
        {/* Main Content */}
        <h1 className="text-3xl font-bold mb-4">Portfolio Dashboard</h1>
        <EstimatedCost />

        {/* Portfolio Items */}
        <div className="grid grid-cols-1 gap-4 mb-8">
          {portfolio.map((item) => (
            <div
              key={item.tokenId}
              className="bg-white rounded-md shadow-md p-4 hover:shadow-lg transition duration-300"
            >
              <h3 className="text-xl font-semibold mb-2">{item.name}</h3>
              <p className="text-gray-700">NFT Type: {item.nftType}</p>
              <p className="text-gray-700">Quantity: {item.quantity}</p>
              <p className="text-gray-700">Price: ${item.price}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default PortfolioDashboard;