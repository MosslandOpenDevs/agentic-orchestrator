import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface PortfolioItem {
  tokenId: string;
  name: string;
  image: string;
  quantity: number;
  price: number;
}

interface PortfolioDashboardProps {
  initialPortfolio?: PortfolioItem[];
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialPortfolio = [] }) => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>(initialPortfolio);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: PortfolioItem[] = [
          { tokenId: 'NFT1', name: 'CryptoPunks', image: '/cryptoPunks.png', quantity: 2, price: 2000 },
          { tokenId: 'NFT2', name: 'Bored Ape Yacht Club', image: '/boredApe.png', quantity: 1, price: 15000 },
          { tokenId: 'NFT3', name: 'Azuki', image: '/azuki.png', quantity: 3, price: 8000 },
        ];
        setPortfolio(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        console.error('Error fetching portfolio data:', err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const totalPortfolioValue = portfolio.reduce((sum, item) => sum + item.quantity * item.price, 0);

  return (
    <div className="container mx-auto p-4">
      {loading && <p>Loading portfolio...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {portfolio.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {portfolio.map((item) => (
            <div key={item.tokenId} className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg">
              <img src={item.image} alt={item.name} className="w-full h-48 object-cover rounded-lg mb-3" aria-label={item.name} />
              <h3 className="text-xl font-semibold mb-2">{item.name}</h3>
              <p className="text-gray-700">Quantity: {item.quantity}</p>
              <p className="text-gray-700">Price: ${item.price.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 text-center">
        <p className="text-3xl font-bold">Total Portfolio Value: ${totalPortfolioValue.toFixed(2)}</p>
      </div>

      {/* Rebalancing Recommendations (Placeholder) */}
      <div className="mt-8 text-center">
        <p>Rebalancing recommendations would go here.</p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;