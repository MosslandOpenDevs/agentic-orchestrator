import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFT {
  id: string;
  name: string;
  image: string;
  price: number;
  quantity: number;
}

interface PortfolioState {
  portfolio: NFT[];
  loading: boolean;
  error: string | null;
}

const PortfolioManagementPage = () => {
  const [portfolio, setPortfolio] = useState<NFT[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: NFT[] = [
          { id: '1', name: 'NFT 1', image: 'https://via.placeholder.com/150', price: 100, quantity: 2 },
          { id: '2', name: 'NFT 2', image: 'https://via.placeholder.com/150', price: 200, quantity: 1 },
          { id: '3', name: 'NFT 3', image: 'https://via.placeholder.com/150', price: 300, quantity: 3 },
        ];
        setPortfolio(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleAddNFT = (nft: NFT) => {
    setPortfolio([...portfolio, nft]);
  };

  const handleRemoveNFT = (id: string) => {
    setPortfolio(portfolio.filter((nft) => nft.id !== id));
  };

  if (loading) {
    return <div>Loading portfolio...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">NFT Portfolio</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {portfolio.map((nft) => (
          <div
            key={nft.id}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`NFT ${nft.name}`}
          >
            <img src={nft.image} alt={nft.name} className="w-full h-48 object-cover rounded-lg mb-3" />
            <h2 className="text-xl font-semibold mb-2">{nft.name}</h2>
            <p className="text-gray-700">Price: ${nft.price}</p>
            <p className="text-gray-700">Quantity: {nft.quantity}</p>
            <button
              onClick={() => handleRemoveNFT(nft.id)}
              className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-4"
              aria-label={`Remove ${nft.name}`}
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={() => router.push('/add-nft')}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
        aria-label="Add NFT"
      >
        Add NFT
      </button>
    </div>
  );
};

export default PortfolioManagementPage;