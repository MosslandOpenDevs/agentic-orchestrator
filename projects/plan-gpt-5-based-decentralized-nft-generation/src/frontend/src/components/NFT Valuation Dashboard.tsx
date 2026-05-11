import React, { useState, useEffect } from 'react';
import { useDebounce } from 'use-lodash-debounce';

// Define interfaces for NFT and ValuationData
interface NFT {
  tokenId: string;
  name: string;
  imageUri: string;
  price: number;
}

interface ValuationData {
  floorPrice: number;
  volume24h: number;
  marketCap: number;
  lastSalePrice: number;
  listings: number;
}

interface NFTValuationDashboardProps {
  nfts: NFT[];
  // Optional:  Fetch data from an API
  fetchData: () => Promise<void>;
}

const NFTValuationDashboard: React.FC<NFTValuationDashboardProps> = ({ nfts, fetchData }) => {
  const [valuationData, setValuationData] = useState<ValuationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sortedNFTs, setSortedNFTs] = useState<NFT[]>(nfts);

  const debouncedFetchData = useDebounce(fetchData, 500);

  useEffect(() => {
    if (debouncedFetchData) {
      debouncedFetchData();
    }
  }, [debouncedFetchData]);

  useEffect(() => {
    if (valuationData) {
      setLoading(false);
    }
  }, [valuationData]);

  useEffect(() => {
    if (!valuationData) {
      setLoading(true);
      setError(null);
    }
  }, [valuationData]);

  const sortNFTs = (sortBy: 'tokenId' | 'price' | 'volume24h') => {
    const sorted = [...sortedNFTs].sort((a, b) => {
      if (sortBy === 'tokenId') {
        return a.tokenId.localeCompare(b.tokenId);
      } else if (sortBy === 'price') {
        return a.price - b.price;
      } else if (sortBy === 'volume24h') {
        return b.volume24h - a.volume24h;
      }
      return 0;
    });
    setSortedNFTs(sorted);
  };

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-lg font-bold text-gray-700">Loading Valuation...</div>
        <div className="mt-4">
          {nfts.map((nft) => (
            <div key={nft.tokenId} className="p-2 rounded-md hover:shadow-sm">
              <img src={nft.imageUri} alt={nft.name} className="w-20 h-20 object-cover rounded-full mr-2" aria-label={nft.name} />
              <p className="text-gray-700">{nft.name}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-lg font-bold text-red-700">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
      <div className="text-lg font-bold text-gray-700 mb-4">NFT Valuation Dashboard</div>
      <div className="mb-4">
        <button onClick={() => sortNFTs('tokenId')} className="bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded-md mr-2">
          Sort by Token ID
        </button>
        <button onClick={() => sortNFTs('price')} className="bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded-md mr-2">
          Sort by Price
        </button>
        <button onClick={() => sortNFTs('volume24h')} className="bg-gray-200 hover:bg-gray-300 px-3 py-2 rounded-md">
          Sort by Volume (24h)
        </button>
      </div>
      <div className="mt-4">
        {sortedNFTs.map((nft) => (
          <div key={nft.tokenId} className="p-2 rounded-md hover:shadow-sm">
            <img src={nft.imageUri} alt={nft.name} className="w-20 h-20 object-cover rounded-full mr-2" aria-label={nft.name} />
            <p className="text-gray-700">{nft.name}</p>
            <p className="text-sm text-gray-600">Floor Price: ${valuationData?.floorPrice || 'N/A'}</p>
            <p className="text-sm text-gray-600">Volume (24h): {valuationData?.volume24h || 'N/A'} </p>
            <p className="text-sm text-gray-600">Last Sale Price: ${valuationData?.lastSalePrice || 'N/A'}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NFTValuationDashboard;