import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTDetails {
  name: string;
  image: string;
  metadata: any;
  owner: string;
}

interface NFTDetailsViewProps {
  nft: NFTDetails;
  isLoading: boolean;
  error?: string;
}

const NFTDetailsView: React.FC<NFTDetailsViewProps> = ({ nft, isLoading, error }) => {
  const { asPath } = useRouter();
  const { name, image, metadata, owner } = nft;
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return <div>Loading NFT Details...</div>;
  }

  if (error) {
    return <div>Error loading NFT Details: {error}</div>;
  }

  return (
    <div className="max-w-screen-md mx-auto p-4 rounded-lg shadow-md bg-white">
      {isMounted && (
        <div className="relative">
          <img
            src={image}
            alt={`NFT ${name}`}
            className="w-full h-56 object-cover rounded-lg"
            aria-label={`NFT ${name}`}
          />

          <div className="p-4">
            <h1 className="text-2xl font-bold text-gray-800">{name}</h1>
            <p className="text-gray-700">
              Owner: {owner}
            </p>

            {/* Metadata Display - Example, adjust based on metadata structure */}
            {metadata && (
              <div className="mt-4">
                <p className="text-gray-700 font-semibold">Metadata:</p>
                <pre className="bg-gray-100 p-2 rounded-md">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NFTDetailsView;