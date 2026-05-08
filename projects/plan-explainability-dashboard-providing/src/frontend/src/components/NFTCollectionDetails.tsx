import React, { useState, useEffect } from 'react';

interface NFTCollection {
  name: string;
  symbol: string;
  image: string;
  description: string;
  attributes: Attribute[];
  floorPrice: number;
  totalSupply: number;
}

interface Attribute {
  name: string;
  type: 'string' | 'number' | 'boolean';
  value: any;
  count: number;
}

interface NFTCollectionDetailsProps {
  collection: NFTCollection | null;
  portfolioHoldings: { [tokenId: string]: number } | null;
}

const NFTCollectionDetails: React.FC<NFTCollectionDetailsProps> = ({ collection, portfolioHoldings }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!collection) {
      setLoading(false);
      setError('Collection data not loaded.');
      return;
    }

    setLoading(true);
    setError(null);
  }, [collection]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex">
      {/* Collection Info */}
      <div className="w-full">
        <img
          src={collection.image}
          alt={`NFT Collection ${collection.name}`}
          aria-label={`NFT Collection ${collection.name}`}
          className="w-full h-48 object-cover rounded-lg mb-4"
        />
        <h1 className="text-2xl font-bold text-gray-800">{collection.name}</h1>
        <p className="text-gray-700">{collection.symbol}</p>
        <p className="text-gray-600">{collection.description}</p>

        {/* Attributes */}
        <div className="mt-6">
          <h2 className="text-lg font-bold text-gray-800 mb-2">Attributes</h2>
          {collection.attributes.map((attr) => (
            <div key={attr.name} className="mb-2 flex items-center">
              <span className="text-gray-700 mr-2">{attr.name}:</span>
              <span className="text-gray-800">{attr.value}</span>
            </div>
          ))}
        </div>

        {/* Floor Price */}
        <div className="mt-4">
          <p className="text-xl font-bold text-gray-800">Floor Price: ${collection.floorPrice}</p>
        </div>

        {/* Total Supply */}
        <div className="mt-4">
          <p className="text-xl font-bold text-gray-800">Total Supply: {collection.totalSupply}</p>
        </div>
      </div>

      {/* Portfolio Holdings */}
      <div className="w-full">
        <h2 className="text-lg font-bold text-gray-800 mb-2">Portfolio Holdings</h2>
        {portfolioHoldings ? (
          <>
            {Object.entries(portfolioHoldings).map(([tokenId, quantity]) => (
              <div key={tokenId} className="flex items-center mb-2">
                <span className="text-gray-700 mr-2">Token ID:</span>
                <span className="text-gray-800">{tokenId}</span>
                <span className="text-gray-700 mr-2">Quantity:</span>
                <span className="text-gray-800">{quantity}</span>
              </div>
            ))}
          </>
        ) : (
          <p className="text-gray-600">No holdings found.</p>
        )}
      </div>
    </div>
  );
};

export default NFTCollectionDetails;