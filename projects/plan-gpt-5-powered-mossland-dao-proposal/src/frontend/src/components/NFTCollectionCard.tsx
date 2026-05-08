import React, { useState, useEffect } from 'react';

interface NFTCollectionCardProps {
  collection: {
    name: string;
    tokenCount: number;
    price: number;
    imageUrl?: string;
  };
  isLoading: boolean;
  onError: (error: string) => void;
}

const NFTCollectionCard: React.FC<NFTCollectionCardProps> = ({
  collection,
  isLoading,
  onError,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!isLoading && !collection) {
      onError('Collection data not loaded.');
    }
  }, [isLoading, collection, onError]);

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className="rounded-lg shadow-md overflow-hidden transition-transform duration-300 ease-in-out hover:scale-x-105 sm:hover:scale-x-110"
      aria-expanded={isExpanded}
      role="region"
      aria-labelledby="collapsible-collection-header"
      onClick={toggleExpand}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          toggleExpand();
        }
      }}
    >
      {isLoading && <p className="text-gray-500 p-4">Loading...</p>}
      {!isLoading && !collection && <p className="text-gray-500 p-4">No collection data available.</p>}
      {isLoading && !collection ? (
        <p className="text-gray-500 p-4">Loading...</p>
      ) : (
        <div className="relative">
          {collection.imageUrl && (
            <img
              src={collection.imageUrl}
              alt={`Collection ${collection.name}`}
              className="w-full h-48 object-cover sm:h-64"
            />
          )}
          <button className="text-left w-full block h-full" id="collapsible-collection-header">
            <div className="flex items-center justify-between p-4">
              <h3 className="text-lg font-medium">{collection.name}</h3>
              <span className="text-gray-600">
                {collection.tokenCount} tokens
              </span>
            </div>
          </button>
          {isExpanded && (
            <div className="p-4">
              <p className="text-sm text-gray-700">
                Price: ${collection.price}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NFTCollectionCard;