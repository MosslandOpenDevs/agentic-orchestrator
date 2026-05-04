import React, { useState, useEffect } from 'react';

interface NFTDetailsProps {
  nftMetadata: {
    name: string;
    description?: string;
    image?: string;
    tokenId?: string;
    contractAddress?: string;
    attributes?: any[];
  };
  ownerAddress?: string;
}

const NFTDetails: React.FC<NFTDetailsProps> = ({ nftMetadata, ownerAddress }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    try {
      // Simulate fetching ownership data (replace with actual API call)
      // This is just a placeholder for demonstration.
      const simulatedOwnerData = ownerAddress ? `Owned by: ${ownerAddress}` : 'Not yet owned';

      setLoading(false);
    } catch (err) {
      setError(err as string);
      setLoading(false);
    }
  }, [ownerAddress]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading NFT Details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p>Error loading NFT details: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex">
      {nftMetadata.image && (
        <img
          src={nftMetadata.image}
          alt={nftMetadata.name}
          className="w-full h-full object-cover rounded-lg"
        />
      )}

      <div className="flex flex-grow items-center justify-around">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{nftMetadata.name}</h2>
          {nftMetadata.description && <p className="text-gray-700">{nftMetadata.description}</p>}
          {nftMetadata.tokenId && <p className="text-gray-700">Token ID: {nftMetadata.tokenId}</p>}
          {nftMetadata.contractAddress && <p className="text-gray-700">Contract Address: {nftMetadata.contractAddress}</p>}

          {nftMetadata.attributes && (
            <div className="mt-4 space-y-2">
              {nftMetadata.attributes.map((attr) => (
                <div key={attr.name} className="flex items-center space-x-2">
                  <span className="text-gray-700">{attr.name}:</span>
                  <span className="text-gray-800">{attr.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          {ownerAddress ? (
            <p
              className="text-xl font-bold text-green-600"
              aria-label={simulatedOwnerData}
              tabIndex={0}
            >
              {simulatedOwnerData}
            </p>
          ) : (
            <p className="text-xl font-bold text-gray-600">Not yet owned</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default NFTDetails;