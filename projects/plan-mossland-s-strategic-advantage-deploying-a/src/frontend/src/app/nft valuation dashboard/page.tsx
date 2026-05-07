import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';

interface NFTValuationData {
  name: string;
  tokenId: string;
  floorPrice: number;
  currentPrice: number;
  image?: string;
}

interface NFTValuationDashboardProps {
  nftAddress: string;
}

const NFTValuationDashboard: React.FC<NFTValuationDashboardProps> = ({ nftAddress }) => {
  const {
    data: nftData,
    isLoading,
    isError,
    error,
  } = useQuery<NFTValuationData | null, Error>(
    () =>
      fetch(`https://api.openseai.com/nft/${nftAddress}`)
        .then((res) => res.json())
        .catch((err) => err),
    'nft-valuation-data'
  );

  if (isLoading) {
    return <div>Loading NFT Valuation...</div>;
  }

  if (isError) {
    return (
      <div>
        Error fetching NFT valuation: {error?.message}
      </div>
    );
  }

  if (!nftData) {
    return <div>No NFT data found.</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-800">NFT Valuation</h1>
        <button className="text-gray-500 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2">
          <ArrowLeft className="mr-2" /> Back
        </button>
      </div>

      <div className="flex items-center mb-6">
        <img
          src={nftData.image || 'https://via.placeholder.com/250'}
          alt={nftData.name}
          className="w-32 h-32 object-cover rounded-full mr-4"
        />
        <div className="flex-grow">
          <p className="text-xl font-bold text-gray-800">{nftData.name}</p>
          <p className="text-gray-700">Token ID: {nftData.tokenId}</p>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xl font-bold text-gray-800">Floor Price:</p>
        <p className="text-gray-700 font-semibold">{nftData.floorPrice} $</p>
      </div>

      <div className="mb-4">
        <p className="text-xl font-bold text-gray-800">Current Price:</p>
        <p className="text-gray-700 font-semibold">{nftData.currentPrice} $</p>
      </div>

      <p className="text-gray-700">
        Data provided by OpenSea.
      </p>
    </div>
  );
};

export default NFTValuationDashboard;