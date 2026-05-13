import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFT {
  name: string;
  tokenId: string;
  collection: string;
  image: string;
  price: number;
  saleHash: string;
}

interface NFTPortfolioProps {
  nfts: NFT[];
  loading?: boolean;
  error?: string;
}

const NFTPortfolio: React.FC<NFTPortfolioProps> = ({ nfts, loading = false, error }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const collectionFilter = searchParams.get('collection');

  const [filteredNfts, setFilteredNfts] = useState<NFT[]>(nfts);

  useEffect(() => {
    if (collectionFilter) {
      const filtered = nfts.filter((nft) => nft.collection === collectionFilter);
      setFilteredNfts(filtered);
    } else {
      setFilteredNfts(nfts);
    }
  }, [nfts, collectionFilter]);

  if (loading) {
    return <div>Loading NFT Portfolio...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!filteredNfts || filteredNfts.length === 0) {
    return <div>No NFTs found.</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4">NFT Portfolio</h1>

      {/* Filter Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700">Filter by Collection:</label>
        <input
          type="text"
          className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Collection Name"
          value={collectionFilter || ''}
          onChange={(e) => setSearchParams({ collection: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredNfts.map((nft) => (
          <div
            key={nft.tokenId}
            className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`NFT: ${nft.name}`}
          >
            <img
              src={nft.image}
              alt={`NFT ${nft.name}`}
              className="w-full h-48 object-cover"
            />
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-2">{nft.name}</h3>
              <p className="text-gray-600">Token ID: {nft.tokenId}</p>
              <p className="text-gray-600">Collection: {nft.collection}</p>
              <p className="text-blue-500 font-bold">Price: ${nft.price}</p>
              {nft.saleHash && <p className="text-gray-600">Sale Hash: {nft.saleHash}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NFTPortfolio;