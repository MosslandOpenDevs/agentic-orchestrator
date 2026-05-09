import React, { useState, useEffect } from 'react';

interface NFTDetailProps {
  nft: {
    name: string;
    description?: string;
    image?: string;
    tokenId?: string;
    metadata?: any;
    domain?: string;
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

  if (!nft || !nft.name) {
    return <div>No NFT data available.</div>;
  }

  const handleDomainClick = () => {
    if (nft.domain && window.open) {
      window.open(`https://${nft.domain}`, '_blank');
    } else {
      console.warn('Could not open domain link.');
    }
  };

  return (
    <div
      className="max-w-4xl mx-auto p-6 rounded-lg shadow-md overflow-hidden"
      aria-label="NFT Detail"
      tabIndex={0}
    >
      {/* NFT Metadata Display */}
      <h1 className="text-2xl font-bold mb-4">{nft.name}</h1>

      {nft.description && (
        <p className="text-gray-700 mb-4">{nft.description}</p>
      )}

      {nft.image && (
        <img
          src={nft.image}
          alt={`NFT ${nft.name}`}
          className="w-full h-48 object-cover rounded-md mb-4"
        />
      )}

      {nft.tokenId && (
        <p className="text-gray-600 font-semibold">Token ID: {nft.tokenId}</p>
      )}

      {nft.metadata && typeof nft.metadata === 'object' && nft.metadata !== null && nft.metadata.attributes && nft.metadata.attributes.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-bold mb-2">Metadata Attributes:</h3>
          {nft.metadata.attributes.map((attr) => (
            <div key={attr.name} className="flex items-center space-x-2">
              <span className="text-gray-700">{attr.name}:</span>
              <span className="text-gray-600">{attr.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Domain Link */}
      <a
        href={`https://${nft.domain}`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800 font-semibold"
        aria-label={`Open Mossland ENS domain: ${nft.domain}`}
        onClick={handleDomainClick}
      >
        View Domain
      </a>
    </div>
  );
};

export default NFTDetail;