import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTDetailsProps {
  nftId: string;
  nftMetadata: NFTMetadata;
  marketPrice: number;
  tradingHistory: TradingHistoryItem[];
}

interface NFTMetadata {
  name: string;
  description: string;
  image: string;
  attributes: Attribute[];
}

interface Attribute {
  trait: string;
  value: string;
  displayType: DisplayType;
}

enum DisplayType {
  TEXT = 'text',
  IMAGE = 'image',
  NUMBER = 'number',
}

interface TradingHistoryItem {
  timestamp: string;
  price: number;
  buyer: string;
  seller: string;
}

const NFTDetails = ({
  nftId,
  nftMetadata,
  marketPrice,
  tradingHistory,
}: NFTDetailsProps) => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (nftId) {
      setLoading(true);
      try {
        // Simulate fetching data - replace with actual API calls
        const fetchedMetadata = nftMetadata;
        const fetchedPrice = marketPrice;
        const fetchedHistory = tradingHistory;

        setLoading(false);
      } catch (err) {
        setError(String(err));
        setLoading(false);
      }
    }
  }, [nftId]);

  if (loading) {
    return <div>Loading NFT Details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-8 rounded-lg shadow-md flex">
      {nftMetadata && nftMetadata.image && (
        <img
          src={nftMetadata.image}
          alt={nftMetadata.name}
          className="w-full h-auto rounded-lg"
          aria-label={nftMetadata.name}
        />
      )}

      <div className="flex flex-col flex-grow">
        <h2 className="text-xl font-bold mb-4">{nftMetadata?.name}</h2>
        <p className="text-gray-700 mb-4">{nftMetadata?.description}</p>

        {nftMetadata?.attributes && nftMetadata?.attributes.map((attr) => (
          <div key={attr.trait} className="mb-4 border-b border-gray-200 p-4">
            <span className="font-semibold">{attr.trait}:</span>
            <span className="text-gray-700">{attr.value}</span>
            {attr.displayType === 'image' && (
              <img
                src={attr.value}
                alt={attr.trait}
                className="w-12 h-12 rounded-full mt-2"
                aria-label={attr.trait}
              />
            )}
          </div>
        ))}

        <p className="text-xl font-bold mb-4">Market Price: ${marketPrice}</p>

        <h3>Trading History</h3>
        {tradingHistory.length > 0 ? (
          <ul className="list-disc pl-4 mb-4">
            {tradingHistory.map((item, index) => (
              <li
                key={index}
                className="text-gray-700"
                aria-label={`Trade on ${new Date(item.timestamp).toLocaleString()}`}
              >
                {new Date(item.timestamp).toLocaleString()} - {item.price} - {item.buyer} - {item.seller}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-700">No trading history available.</p>
        )}
      </div>
    </div>
  );
};

export default NFTDetails;