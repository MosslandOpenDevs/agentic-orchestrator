import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTMetadata {
  name: string;
  description: string;
  image: string;
  attributes: Attribute[];
}

interface Attribute {
  trait: string;
  value: string | number;
  displayType: DisplayType;
}

enum DisplayType {
  TEXT = 'text',
  NUMBER = 'number',
  IMAGE = 'image',
}

interface MarketData {
  price: number;
  floorPrice: number;
  volume24h: number;
}

interface GPT5Prediction {
  prediction: string;
  confidence: number;
}

const NFTDetails = ({
  nftMetadata,
  marketData,
  gpt5Prediction,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!nftMetadata || !marketData || !gpt5Prediction) {
      setLoading(false);
      setError('Failed to load NFT details.');
      return;
    }

    setLoading(false);
  }, [nftMetadata, marketData, gpt5Prediction]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading NFT details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8 rounded-lg shadow-md bg-white">
      <h1 className="text-2xl font-bold mb-4">{nftMetadata.name}</h1>

      <img
        src={nftMetadata.image}
        alt={`NFT ${nftMetadata.name}`}
        className="w-full h-56 object-cover rounded-md mb-4"
        aria-label={`Image of ${nftMetadata.name}`}
      />

      <p className="text-gray-700 mb-4">
        {nftMetadata.description}
      </p>

      <div className="mb-4">
        <h2>Attributes</h2>
        <ul className="list-disc pl-4">
          {nftMetadata.attributes.map((attribute) => (
            <li
              key={attribute.trait}
              className="text-gray-700"
              aria-label={`Attribute: ${attribute.trait}`}
            >
              {attribute.trait}: {attribute.value}
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-4">
        <h2>Market Data</h2>
        <p className="text-gray-700">Price: ${marketData.price.toFixed(2)}</p>
        <p className="text-gray-700">Floor Price: ${marketData.floorPrice.toFixed(2)}</p>
        <p className="text-gray-700">Volume (24h): {marketData.volume24h}</p>
      </div>

      <div className="mb-4">
        <h2>GPT-5 Prediction</h2>
        <p className="text-gray-700">
          Prediction: {gpt5Prediction.prediction}
        </p>
        <p className="text-gray-700">
          Confidence: {gpt5Prediction.confidence.toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export default NFTDetails;