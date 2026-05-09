import React, { useState, useEffect } from 'react';

interface NFTCardProps {
  nftMetadata: {
    name: string;
    image: string;
    tokenId: string;
    collection: string;
    description?: string;
  };
  gpt5Valuation?: number;
  riskAssessment: number;
}

const NFTCard: React.FC<NFTCardProps> = ({
  nftMetadata,
  gpt5Valuation,
  riskAssessment,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Simulate GPT-5 valuation fetching (replace with actual API call)
    const fetchGPT5Valuation = async () => {
      try {
        // Replace with your actual GPT-5 API call
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
        const valuation = Math.random() * 1000;
        setLoading(false);
        setGPT5Valuation(valuation);
      } catch (err) {
        setError('Failed to fetch GPT-5 valuation');
        setLoading(false);
      }
    };

    fetchGPT5Valuation();
  }, [gpt5Valuation]);

  const riskIndicatorColor = riskAssessment > 70 ? 'red' : riskAssessment < 30 ? 'green' : 'orange';

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-lg shadow-md overflow-hidden ${riskIndicatorColor}`}
      aria-label={`NFT Card for ${nftMetadata.name}`}
      tabIndex={0}
    >
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}
      <img
        src={nftMetadata.image}
        alt={nftMetadata.name}
        className="w-full h-48 object-cover rounded-lg"
      />
      <h3 className="text-xl font-bold mt-4">{nftMetadata.name}</h3>
      <p className="text-gray-600 mt-2">
        Token ID: {nftMetadata.tokenId}
      </p>
      <p className="text-gray-600 mt-2">
        Collection: {nftMetadata.collection}
      </p>
      {nftMetadata.description && (
        <p className="text-gray-700 mt-4 px-4 pt-2">
          {nftMetadata.description}
        </p>
      )}
      {gpt5Valuation !== undefined && (
        <p className="text-2xl font-semibold mt-4">
          GPT-5 Valuation: ${gpt5Valuation}
        </p>
      )}
      <div className="mt-4 flex items-center">
        <p className="text-gray-600 mr-2">Risk Assessment:</p>
        <div className="progress-bar" style={{ width: `${riskAssessment}%` }}>
          <span className="absolute top-0 left-0 w-full h-full bg-blue-500 opacity-0"></span>
        </div>
      </div>
    </div>
  );
};

export default NFTCard;