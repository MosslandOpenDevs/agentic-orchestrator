import React, { useState, useEffect } from 'react';

interface NFTCardProps {
  nft: {
    name: string;
    image: string;
    description?: string;
    price: number;
    floorPrice?: number;
    volume?: number;
    tokenId?: number;
  };
  valuationData?: {
    valuation: number;
    source: string;
  };
  riskData?: {
    riskLevel: 'low' | 'medium' | 'high';
    description: string;
  };
}

const NFTCard: React.FC<NFTCardProps> = ({ nft, valuationData, riskData }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Simulate fetching data (replace with actual API calls)
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, [nft]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-center">Loading NFT Card...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md text-red-700 flex flex-col items-center">
        <div className="text-center">Error loading NFT data: {error}</div>
      </div>
    );
  }

  const valuationText =
    valuationData && valuationData.valuation
      ? `Valuation: ${valuationData.valuation} (${valuationData.source})`
      : 'Valuation: N/A';

  const riskLevelText =
    riskData && riskData.riskLevel
      ? `${riskData.riskLevel.toUpperCase()} Risk: ${riskData.description}`
      : 'Risk: N/A';

  return (
    <div className="bg-white p-4 rounded-lg shadow-md flex flex-row items-center">
      <img
        src={nft.image}
        alt={nft.name}
        className="w-32 h-32 object-cover rounded-md mr-4"
        aria-label={nft.name}
        role="img"
      />
      <div className="flex-1">
        <h3 className="text-lg font-semibold mb-2">{nft.name}</h3>
        <p className="text-gray-700 mb-2">{nft.description || 'No description available.'}</p>
        <p className="text-gray-700 mb-2">Token ID: {nft.tokenId || 'N/A'}</p>
        <p className="text-xl font-bold">{valuationText}</p>
        <p className="text-gray-700">{riskLevelText}</p>
      </div>
    </div>
  );
};

export default NFTCard;