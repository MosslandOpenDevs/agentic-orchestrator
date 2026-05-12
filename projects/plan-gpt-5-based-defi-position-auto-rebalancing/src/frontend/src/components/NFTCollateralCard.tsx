import React, { useState, useEffect } from 'react';

interface NFTCollateralCardProps {
  asset: {
    name: string;
    symbol: string;
    quantity: number;
    value: number;
    ratio: number;
    assetId: string;
  };
  isLoading: boolean;
  onError: (error: string) => void;
}

const NFTCollateralCard: React.FC<NFTCollateralCardProps> = ({
  asset,
  isLoading,
  onError,
} ) => {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (asset.quantity === 0) {
      setIsExpanded(true);
    }
  }, [asset, isLoading]);

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div
      className="flex flex-col w-full max-w-sm rounded-lg shadow-md overflow-hidden transition-transform duration-300 ease-in-out hover:scale-x-105"
      aria-expanded={isExpanded}
      role="region"
      aria-labelledby="collapsible-heading"
    >
      {isLoading && <p>Loading...</p>}
      {asset.quantity === 0 && (
        <button
          onClick={toggleExpand}
          className="text-left bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2"
          aria-expanded={isExpanded}
          aria-controls="collapsible-content"
        >
          {asset.name} (0)
        </button>
      )}

      {isExpanded && (
        <div className="bg-white p-4" aria-hidden="true">
          <h2 id="collapsible-heading" className="text-lg font-bold text-gray-800">
            {asset.name} ({asset.symbol})
          </h2>
          <p className="text-gray-700">
            Quantity: {asset.quantity}
          </p>
          <p className="text-gray-700">
            Value: ${asset.value.toFixed(2)}
          </p>
          <p className="text-gray-700">
            Ratio: 1: {asset.ratio.toFixed(2)}
          </p>
          <p className="text-gray-700">
            Asset ID: {asset.assetId}
          </p>
        </div>
      )}

      {asset.quantity > 0 && (
        <button
          onClick={toggleExpand}
          className="text-left bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2"
          aria-expanded={isExpanded}
          aria-controls="collapsible-content"
        >
          {asset.name} ({asset.symbol})
        </button>
      )}

      {onError && <div className="text-red-500 p-2">{asset.error}</div>}
    </div>
  );
};

export default NFTCollateralCard;