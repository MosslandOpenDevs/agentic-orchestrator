import React, { useState, useEffect } from 'react';

interface NFTDetailProps {
  nft: {
    tokenId: string;
    name: string;
    description?: string;
    image?: string;
    valuation?: number;
    // Add other NFT properties here as needed
  };
  isLoading: boolean;
  error?: string | null;
}

const NFTDetail: React.FC<NFTDetailProps> = ({ nft, isLoading, error }) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return <div>Loading NFT Details...</div>;
  }

  if (error) {
    return <div>Error loading NFT: {error}</div>;
  }

  if (!nft) {
    return <div>No NFT data available.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 rounded-lg shadow-md overflow-hidden bg-white">
      {/* NFT Image */}
      {nft.image && (
        <img
          src={nft.image}
          alt={`NFT ${nft.tokenId}`}
          className="w-full h-48 object-cover rounded-lg mb-4"
          aria-label={`NFT ${nft.tokenId} image`}
        />
      )}

      {/* NFT Details */}
      <h2 className="text-xl font-bold mb-2">{nft.name}</h2>
      {nft.description && <p className="text-gray-700 mb-4">{nft.description}</p>}

      {/* Valuation Display */}
      {nft.valuation !== undefined && (
        <div className="text-3xl font-semibold text-emerald-600 mb-4">
          Valuation: ${nft.valuation}
        </div>
      )}

      {/* Additional details can be added here */}
    </div>
  );
};

export default NFTDetail;