import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTHolding {
  tokenId: string;
  name: string;
  image: string;
  price: number;
  priceHistory: { date: string; price: number }[];
}

interface NFTHoldingDetailsProps {
  nftHolding: NFTHolding;
}

const NFTHoldingDetails = ({ nftHolding }: NFTHoldingDetailsProps) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (nftHolding) {
      setLoading(true);
      // Simulate fetching price history (replace with actual API call)
      const fetchPriceHistory = async () => {
        const fakePriceHistory = [
          { date: '2023-10-26', price: 1.2 },
          { date: '2023-10-27', price: 1.3 },
          { date: '2023-10-28', price: 1.25 },
        ];
        setTimeout(() => {
          setLoading(false);
        }, 1000);
      };
      fetchPriceHistory();
    }
  }, [nftHolding]);

  if (loading) {
    return <div>Loading NFT Details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-8 rounded-lg shadow-md bg-white">
      {/* NFT Image */}
      <img
        src={nftHolding.image}
        alt={nftHolding.name}
        aria-label={nftHolding.name}
        className="w-full h-56 object-cover rounded-lg"
      />

      {/* NFT Details */}
      <div className="p-4">
        <h2 className="text-xl font-bold mb-2">{nftHolding.name}</h2>
        <p className="text-gray-700 mb-2">Token ID: {nftHolding.tokenId}</p>
        <p className="text-gray-700 mb-2">Price: ${nftHolding.price.toFixed(2)}</p>
      </div>

      {/* Price History */}
      <div className="p-4">
        <h3 className="text-lg font-bold mb-2">Price History</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {nftHolding.priceHistory.map((historyItem) => (
              <tr key={historyItem.date}>
                <td>{historyItem.date}</td>
                <td>${historyItem.price.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NFTHoldingDetails;