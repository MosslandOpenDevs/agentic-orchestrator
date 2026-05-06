import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFTHolder {
  tokenId: string;
  name: string;
  portfolio: {
    btc: number;
    eth: number;
    usdt: number;
    // Add other supported assets here
  };
  riskProfile: string;
}

interface NFTHolderDetailsProps {
  tokenId: string;
}

const NFTHolderDetails: React.FC<NFTHolderDetailsProps> = ({ tokenId }) => {
  const [nftHolder, setNftHolder] = useState<NFTHolder | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchParams] = useSearchParams();
  const id = searchParams.get('tokenId') || tokenId;

  useEffect(() => {
    const fetchNftHolder = async () => {
      try {
        const response = await fetch(`https://api.example.com/nft/${id}`); // Replace with your API endpoint
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data: NFTHolder = await response.json();
        setNftHolder(data);
        setLoading(false);
        setError(null);
      } catch (error: any) {
        setError(error.message);
        setLoading(false);
      }
    };

    fetchNftHolder();
  }, [id]);

  if (loading) {
    return <div>Loading NFT Holder Details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!nftHolder) {
    return <div>Could not retrieve NFT Holder Details.</div>;
  }

  return (
    <div className="max-w-screen-md mx-auto p-6 rounded-lg shadow-md bg-white">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">{nftHolder.name}</h1>

      <p className="text-gray-700 mb-4">
        Token ID: {nftHolder.tokenId}
      </p>

      <section className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Portfolio Breakdown</h3>
        <div className="flex flex-col md:flex-row">
          <div className="mb-2 md:mb-0">
            <p className="text-gray-700">BTC:</p>
            <p className="text-xl font-semibold">{nftHolder.portfolio.btc} BTC</p>
          </div>
          <div className="mb-2 md:mb-0">
            <p className="text-gray-700">ETH:</p>
            <p className="text-xl font-semibold">{nftHolder.portfolio.eth} ETH</p>
          </div>
          <div className="mb-2 md:mb-0">
            <p className="text-gray-700">USDT:</p>
            <p className="text-xl font-semibold">{nftHolder.portfolio.usdt} USDT</p>
          </div>
        </div>
      </section>

      <section className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Risk Assessment</h3>
        <p className="text-gray-700">{nftHolder.riskProfile}</p>
      </section>
    </div>
  );
};

export default NFTHolderDetails;