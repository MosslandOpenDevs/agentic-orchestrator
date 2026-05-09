import React, { useState, useEffect } from 'react';
import Image from 'next/image';

interface NFTCardProps {
  nft: {
    name: string;
    image: string;
    description?: string;
    attributes?: any[];
    tokenId?: string;
  };
  isLoading: boolean;
  onError: (error: Error) => void;
}

const NFTCard: React.FC<NFTCardProps> = ({ nft, isLoading, onError }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!nft) {
      return;
    }
  }, [nft]);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className="flex flex-col w-full max-w-sm rounded-lg shadow-md overflow-hidden transition-transform duration-300 ease-in-out hover:scale-x-105"
      aria-expanded={isExpanded}
      role="region"
      aria-labelledby={`description-${nft.name}`}
      key={nft.name}
    >
      {isLoading ? (
        <div className="p-4 text-center">
          Loading NFT...
        </div>
      ) : nft.image ? (
        <Image
          src={nft.image}
          alt={nft.name}
          width={300}
          height={300}
          priority
          className="object-cover w-full h-full"
        />
      ) : (
        <div className="p-4 text-center">
          No Image Available
        </div>
      )}

      {nft.description && (
        <div
          className={`p-4 ${isExpanded ? 'max-h-20' : 'max-h-12'} overflow-hidden text-gray-700`}
          role="region"
          aria-labelledby={`description-${nft.name}`}
        >
          <p className="text-lg">{nft.description}</p>
        </div>
      )}

      {nft.attributes && nft.attributes.length > 0 && (
        <div className="p-4 text-sm text-gray-600">
          Attributes:
          <ul>
            {nft.attributes.map((attr) => (
              <li key={attr.name}>
                <strong>{attr.name}:</strong> {attr.value}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default NFTCard;