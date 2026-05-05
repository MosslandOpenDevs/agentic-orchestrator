import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { useRouter } from 'next/router';

// Define interfaces for data models
interface NFT {
  tokenId: string;
  name: string;
  image: string;
  price: number;
  quantity: number;
}

interface PortfolioData {
  portfolioOverview: {
    totalValue: number;
    nftCount: number;
  }
  nfts: NFT[];
}

interface RiskAssessment {
  overallRisk: string;
  details: string;
}

interface RebalanceOptions {
  targetValue: number;
  rebalancePercentage: number;
}


const NFTPortfolioDashboard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const router = useRouter();
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get('tokenId')) {
      // Simulate fetching data based on tokenId
      const tokenId = searchParams.get('tokenId');
      const fetchData = async () => {
        try {
          const data: PortfolioData = {
            portfolioOverview: {
              totalValue: 10000,
              nftCount: 5,
            },
            nfts: [
              { tokenId: 'NFT1', name: 'Mossland NFT 1', image: '/images/nft1.png', price: 2000, quantity: 2 },
              { tokenId: 'NFT2', name: 'Mossland NFT 2', image: '/images/nft2.png', price: 3000, quantity: 1 },
              { tokenId: 'NFT3', name: 'Mossland NFT 3', image: '/images/nft3.png', price: 5000, quantity: 1 },
            ],
          };
          setPortfolioData(data);
          setLoading(false);
        } catch (err) {
          setError('Failed to fetch portfolio data.');
          setLoading(false);
        }
      };

      fetchData();
    } else {
      setPortfolioData(null);
      setLoading(false);
    }
  }, [searchParams]);

  const handleRebalance = (options: RebalanceOptions) => {
    // Placeholder for rebalancing logic
    console.log('Rebalancing with options:', options);
  };

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">NFT Portfolio Dashboard</h1>

      {/* Portfolio Overview */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">Portfolio Overview</h2>
        <p className="text-gray-700">Total Value: ${portfolioData.portfolioOverview.totalValue}</p>
        <p className="text-gray-700">NFT Count: {portfolioData.portfolioOverview.nftCount}</p>
      </div>

      {/* NFT List */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">NFTs</h2>
        <ul className="list-disc pl-4">
          {portfolioData.nfts.map((nft) => (
            <li key={nft.tokenId} className="flex items-center">
              <img src={nft.image} alt={nft.name} className="w-12 h-12 object-cover rounded mr-2" aria-label={nft.name} />
              <span>{nft.name} - ${nft.price} x {nft.quantity}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Risk Assessment */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">Risk Assessment</h2>
        <p className="text-gray-700">Overall Risk: Low</p>
        <p className="text-gray-700">Details:  Based on current market conditions.</p>
      </div>

      {/* Rebalancing Tools */}
      <div className="mb-4">
        <h2 className="text-2xl font-semibold mb-2">Rebalancing Tools</h2>
        <label htmlFor="targetValue" className="block text-gray-700 mb-2">Target Value:</label>
        <input
          type="number"
          id="targetValue"
          className="form-control text-lg mb-4"
          placeholder="Enter target value"
        />
        <label htmlFor="rebalancePercentage" className="block text-gray-700 mb-2">Rebalance Percentage:</label>
        <input
          type="number"
          id="rebalancePercentage"
          className="form-control text-lg mb-4"
          placeholder="Enter rebalance percentage"
        />
        <button onClick={() => handleRebalance({ targetValue: 10000, rebalancePercentage: 10 })} className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">Rebalance</button>
      </div>
    </div>
  );
};

export default NFTPortfolioDashboard;