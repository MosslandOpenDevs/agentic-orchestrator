import React, { useState, useEffect } from 'react';

interface RWAAsset {
  name: string;
  symbol: string;
  price: number;
  blockchain: {
    name: string;
    ticker: string;
  };
}

interface RWADetailsProps {
  asset: RWAAsset;
  isLoading: boolean;
  error?: string;
}

const RWADetails: React.FC<RWADetailsProps> = ({ asset, isLoading, error }) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md text-center">
        <p className="text-lg font-semibold">Loading RWA Details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md text-center">
        <p className="text-lg font-semibold text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md text-center">
      <h1 className="text-2xl font-bold mb-4">{asset.name}</h1>
      <p className="text-xl font-semibold mb-2">Symbol: {asset.symbol}</p>
      <p className="text-3xl font-bold mb-2">Price: ${asset.price}</p>

      <div className="mb-4">
        <p className="text-sm font-semibold">Blockchain:</p>
        <p className="text-base">
          {asset.blockchain.name} ({asset.blockchain.ticker})
        </p>
      </div>

      <div
        className="flex items-center justify-center space-x-2"
        aria-label="RWA Details"
      >
        <p className="text-sm">
          This RWA asset represents a tokenized interest in [Description of asset].
        </p>
      </div>
    </div>
  );
};

export default RWADetails;