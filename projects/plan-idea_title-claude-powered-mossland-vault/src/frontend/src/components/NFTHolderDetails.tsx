import React, { useState, useEffect } from 'react';

interface NFTHolderDetailsProps {
  walletAddress?: string;
  nftHoldings?: NFTHolding[];
  isLoading?: boolean;
  error?: string | null;
}

const NFTHolderDetails = ({
  walletAddress,
  nftHoldings,
  isLoading = false,
  error = null,
}: NFTHolderDetailsProps) => {
  const [holderDetails, setHolderDetails] = useState<any>();

  useEffect(() => {
    if (walletAddress) {
      // Simulate fetching data - Replace with actual API call
      setTimeout(() => {
        const mockNFTHoldings = [
          { tokenId: '1', name: 'Mossland Token', quantity: 1 },
          { tokenId: '2', name: 'Mossland Token', quantity: 2 },
        ];
        setHolderDetails({
          walletAddress: walletAddress,
          nftHoldings: mockNFTHoldings,
        });
      }, 1000);
    }
  }, [walletAddress]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md flex flex-col items-center">
        <p className="text-gray-700 text-lg font-semibold">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md flex flex-col items-center">
        <p className="text-gray-700 text-lg font-semibold">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-md shadow-md flex flex-col items-center">
      {walletAddress && (
        <div className="text-gray-800 text-xl font-bold mb-4">
          Wallet Address: {walletAddress}
        </div>
      )}

      {nftHoldings && (
        <div className="mb-4">
          <h3 className="text-gray-800 text-lg font-semibold mb-2">NFT Holdings:</h3>
          <ul className="list-disc list-inside text-gray-700">
            {nftHoldings.map((holding) => (
              <li
                key={holding.tokenId}
                className="mb-1"
                aria-label={`NFT holding: ${holding.name}`}
              >
                {holding.name} - Quantity: {holding.quantity}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default NFTHolderDetails;