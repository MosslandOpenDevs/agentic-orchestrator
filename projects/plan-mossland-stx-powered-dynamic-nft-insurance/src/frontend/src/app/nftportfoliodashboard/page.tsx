import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { useRouter } from 'next/router';
import { useSnackbar } from 'react-snackbar';

// Define interfaces for data models
interface NFT {
  id: string;
  name: string;
  image: string;
  price: number;
  quantity: number;
}

interface PortfolioOverview {
  totalValue: number;
  nftCount: number;
}

interface RebalanceOptions {
  increasePercentage: number;
}

const NFTPortfolioDashboard: React.FC = () => {
  const [nftData, setNftData] = useState<NFT[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [portfolioValue, setPortfolioValue] = useState<PortfolioOverview>({
    totalValue: 0,
    nftCount: 0,
  });
  const [rebalanceOptions, setRebalanceOptions] = useState<RebalanceOptions>({
    increasePercentage: 0,
  });
  const router = useRouter();
  const { setSnackbar } = useSnackbar();

  useEffect(() => {
    const fetchNftData = async () => {
      try {
        const params = useSearchParams();
        const id = params.get('id');

        const response = await fetch(`/api/nftData?id=${id}`, {
          method: 'GET',
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch NFT data: ${response.statusText}`);
        }

        const data: NFT[] = await response.json();
        setNftData(data);
        setLoading(false);
        calculatePortfolioValue();
      } catch (error) {
        setError(error.message);
        setLoading(false);
      }
    };

    fetchNftData();
  }, []);

  const calculatePortfolioValue = () => {
    let totalValue = 0;
    let nftCount = 0;

    nftData.forEach((nft) => {
      totalValue += nft.price * nft.quantity;
      nftCount++;
    });

    setPortfolioValue({ totalValue, nftCount });
  };

  const handleRebalance = () => {
    // Simulate rebalancing logic (replace with actual implementation)
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSnackbar({
        message: 'Rebalancing complete!',
        type: 'success',
      });
    }, 1500);
  };

  if (loading) {
    return <div>Loading NFT data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">NFT Portfolio Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Portfolio Overview */}
        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h2 className="text-xl font-semibold mb-2">Portfolio Overview</h2>
          <p className="text-gray-700">Total Value: ${portfolioValue.totalValue.toFixed(2)}</p>
          <p className="text-gray-700">NFT Count: {portfolioValue.nftCount}</p>
        </div>

        {/* NFT Detail View */}
        {nftData.length > 0 && (
          <div className="bg-gray-100 p-4 rounded-md shadow-md">
            <h2 className="text-xl font-semibold mb-2">NFT Details</h2>
            {nftData.map((nft) => (
              <div key={nft.id} className="flex items-center mb-2">
                <img src={nft.image} alt={nft.name} className="w-20 h-20 object-cover rounded-md mr-2" aria-label={nft.name} />
                <p className="text-gray-700">{nft.name}</p>
                <p className="text-gray-700">Price: ${nft.price.toFixed(2)}</p>
                <p className="text-gray-700">Quantity: {nft.quantity}</p>
              </div>
            ))}
          </div>
        )}

        {/* Rebalancing Tool */}
        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h2 className="text-xl font-semibold mb-2">Rebalancing Tool</h2>
          <label className="block text-gray-700 mb-2">Increase Percentage:</label>
          <input
            type="number"
            placeholder="Enter percentage"
            value={rebalanceOptions.increasePercentage}
            onChange={(e) =>
              setRebalanceOptions({
                ...rebalanceOptions,
                increasePercentage: parseFloat(e.target.value),
              })
            }
            className="w-full p-2 rounded-md border border-gray-300 text-gray-700 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleRebalance}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
          >
            Rebalance
          </button>
        </div>
      </div>
    </div>
  );
};

export default NFTPortfolioDashboard;