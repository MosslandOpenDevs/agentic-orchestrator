import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFTHolding {
  tokenId: string;
  name: string;
  imageUri: string;
  quantity: number;
  currentPrice: number;
}

interface PortfolioOverviewProps {
  nftHoldings: NFTHolding[];
  yieldRate: number;
  riskTolerance: 'low' | 'medium' | 'high';
}

const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ nftHoldings, yieldRate, riskTolerance }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const userId = searchParams.get('userId') || 'defaultUser'; // Example user ID

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    // Simulate fetching data from an API or database
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-gray-700">Loading Portfolio...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-red-700">Error: {error.message}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
      <h2 className="text-2xl font-bold text-gray-700 mb-4">Portfolio Overview</h2>

      {/* NFT Holdings List */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-700 mb-2">NFT Holdings</h3>
        <ul className="list-disc list-inside space-y-2">
          {nftHoldings.map((holding) => (
            <li key={holding.tokenId} className="p-4 rounded-md border border-gray-300">
              <img src={holding.imageUri} alt={holding.name} className="w-24 h-24 object-cover rounded-md mb-2" aria-label={holding.name} />
              <p className="text-gray-700">{holding.name}</p>
              <p className="text-lg font-semibold">Quantity: {holding.quantity}</p>
              <p className="text-lg font-semibold">Current Price: ${holding.currentPrice.toFixed(2)}</p>
            </li>
          ))}
        </ul>
      </div>

      {/* Yield Rate Display */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-700 mb-2">Yield Rate</h3>
        <p className="text-3xl font-bold text-gray-700">{yieldRate.toFixed(2)}%</p>
      </div>

      {/* Risk Tolerance Indicator */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-700 mb-2">Risk Tolerance</h3>
        <p className="text-xl font-semibold text-amber-500">{riskTolerance}</p>
      </div>
    </div>
  );
};

export default PortfolioOverview;