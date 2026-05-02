import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTDetailsProps {
  nftId: string;
  nftData: NFTData;
}

interface NFTData {
  name: string;
  image: string;
  metadata: Metadata;
  owner: string;
}

interface Metadata {
  description?: string;
  attributes?: Attribute[];
}

interface Attribute {
  name: string;
  value: string;
}

const NFTDetails = ({ nftId, nftData }: NFTDetailsProps) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (nftId) {
      setLoading(true);
      // Simulate fetching data - replace with actual API call
      setTimeout(() => {
        setLoading(false);
      }, 1000);
    }
  }, [nftId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading NFT details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 rounded-lg shadow-md bg-white">
      {/* NFT Image */}
      <img
        src={nftData.image}
        alt={`NFT ${nftData.name}`}
        className="w-full h-56 object-cover rounded-lg"
        aria-label={`NFT ${nftData.name}`}
      />

      {/* Metadata Display */}
      <div className="mt-4">
        <h2 className="text-xl font-bold">{nftData.name}</h2>
        <p className="text-gray-700">Description: {nftData.metadata?.description || 'No description available'}</p>
        {nftData.metadata?.attributes && (
          <div className="mt-2">
            <h3 className="text-lg font-bold">Attributes:</h3>
            <ul className="list-disc pl-2">
              {nftData.metadata.attributes?.map((attribute) => (
                <li key={attribute.name}>
                  {attribute.name}: {attribute.value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Owner Information */}
      <div className="mt-4">
        <p className="text-gray-700 font-bold">Owner:</p>
        <p className="text-lg">{nftData.owner}</p>
      </div>
    </div>
  );
};

export default NFTDetails;