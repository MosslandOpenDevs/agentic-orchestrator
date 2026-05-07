import React, { useState, useEffect } from 'react';

interface NFTPositionCardProps {
  nftData: {
    name: string;
    imageUrl: string;
    quantity: number;
    currentPrice: number;
  };
  profitLoss: number;
  isLoading: boolean;
  onRefresh?: () => void;
}

const NFTPositionCard: React.FC<NFTPositionCardProps> = ({
  nftData,
  profitLoss,
  isLoading,
  onRefresh,
}) => {
  const [price, setPrice] = useState<number>(nftData.currentPrice);
  const [totalValue, setTotalValue] = useState<number>(0);

  useEffect(() => {
    if (!isLoading && nftData) {
      setPrice(nftData.currentPrice);
      setTotalValue(nftData.quantity * nftData.currentPrice);
    }
  }, [nftData, isLoading]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md w-64 flex flex-col items-center">
        <div className="text-center">Loading NFT Position...</div>
      </div>
    );
  }

  if (!nftData) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md w-64 flex flex-col items-center">
        <div className="text-center">NFT Data Not Available</div>
      </div>
    );
  }

  const profitLossText = profitLoss > 0 ? 'Profit' : 'Loss';

  return (
    <div className="bg-white p-4 rounded-lg shadow-md w-64 flex flex-col items-center">
      <img
        src={nftData.imageUrl}
        alt={nftData.name}
        className="w-full h-32 object-cover rounded-md"
        aria-label={nftData.name}
      />
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{nftData.name}</h3>
      <p className="text-gray-600 mb-2">
        Quantity Held: {nftData.quantity}
      </p>
      <p className="text-2xl font-bold text-green-600 mb-2">
        Current Price: ${price.toFixed(2)}
      </p>
      <p className="text-2xl font-bold mb-2">
        {profitLossText}: ${profitLoss.toFixed(2)}
      </p>
    </div>
  );
};

export default NFTPositionCard;