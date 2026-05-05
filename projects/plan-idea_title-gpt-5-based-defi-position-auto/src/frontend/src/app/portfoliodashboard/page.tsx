import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface PortfolioHolding {
  tokenId: string;
  name: string;
  quantity: number;
  price: number;
  totalValue: number;
}

interface PortfolioDashboardProps {
  initialData?: PortfolioHolding[];
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialData = [] }) => {
  const [data, setData] = useState<PortfolioHolding[]>(initialData);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const tokenID = searchParams.get('tokenId');
    if (tokenID) {
      // Simulate fetching data based on tokenId
      const fetchedData: PortfolioHolding[] = [
        { tokenId: tokenID, name: 'Mossland NFT', quantity: 10, price: 100, totalValue: 1000 },
      ];
      setData(fetchedData);
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    // Simulate fetching data from an API
    setTimeout(() => {
      const simulatedData: PortfolioHolding[] = [
        { tokenId: 'mossland1', name: 'Mossland NFT', quantity: 10, price: 100, totalValue: 1000 },
        { tokenId: 'mossland2', name: 'Mossland NFT', quantity: 5, price: 150, totalValue: 750 },
      ];
      setData(simulatedData);
      setIsLoading(false);
    }, 1500);
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">Portfolio Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.map((item) => (
          <div
            key={item.tokenId}
            className="bg-white p-4 rounded-md shadow-sm hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`Details for ${item.name}`}
          >
            <h2 className="text-xl font-semibold mb-2 text-gray-800">{item.name}</h2>
            <p className="text-gray-600">Quantity: {item.quantity}</p>
            <p className="text-gray-600">Price: ${item.price}</p>
            <p className="text-gray-600 font-bold">Total Value: ${item.totalValue}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 text-center">
        <p className="text-gray-600">
          This dashboard displays your portfolio holdings.  You can view performance and manually rebalance (limited functionality).
        </p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;