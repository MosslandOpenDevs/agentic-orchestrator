import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTDetailsProps {
  nftId: string;
  nftData: NFTData;
  isLoading: boolean;
  error?: string;
}

interface NFTData {
  name: string;
  description: string;
  image: string;
  price: number;
  volume: number;
  floorPrice: number;
  prediction: string;
  // Add more NFT metadata fields as needed
}

const NFTDetails = ({ nftId, nftData, isLoading, error }: NFTDetailsProps) => {
  const router = useRouter();

  useEffect(() => {
    if (nftId) {
      router.push(`/nft/${nftId}`);
    }
  }, [nftId, router]);

  if (isLoading) {
    return <div>Loading NFT Details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="max-w-screen-md mx-auto p-8 rounded-lg shadow-md bg-white">
      <h1 className="text-3xl font-bold mb-4 text-center">{nftData.name}</h1>
      <img
        src={nftData.image}
        alt={nftData.name}
        className="w-full h-56 object-cover rounded-md mb-4"
        aria-label={nftData.name}
      />
      <p className="text-gray-700 mb-4">{nftData.description}</p>
      <div className="flex justify-around items-center mb-4">
        <p className="text-xl font-semibold">Price: ${nftData.price}</p>
        <p className="text-xl font-semibold">Volume: {nftData.volume}</p>
      </div>
      <p className="text-xl font-semibold">Floor Price: ${nftData.floorPrice}</p>
      <p className="text-xl font-semibold">Prediction: {nftData.prediction}</p>
    </div>
  );
};

export default NFTDetails;