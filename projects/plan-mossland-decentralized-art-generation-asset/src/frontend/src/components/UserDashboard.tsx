import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFT {
  id: string;
  name: string;
  image: string;
  tokenId: string;
  owner: string;
}

interface UserDashboardProps {
  userId: string;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ userId }) => {
  const [nftList, setNftList] = useState<NFT[]>([]);
  const [transactionHistory, setTransactionHistory] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNFTs = async () => {
      try {
        const response = await fetch(`https://api.openseai.com/nft/${userId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setNftList(data.nfts || []);
      } catch (error) {
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchTransactions = async () => {
      try {
        const response = await fetch(`https://api.openseai.com/transaction/${userId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setTransactionHistory(data.transactions || []);
      } catch (error) {
        setError(error.message);
      }
    };

    fetchNFTs();
    fetchTransactions();
  }, [userId]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading user dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md">
        <p className="text-red-700">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md flex">
      <div className="w-full">
        <h2 className="text-xl font-bold mb-4">NFTs</h2>
        <ul className="list-disc pl-4 mb-4">
          {nftList.map((nft) => (
            <li key={nft.id} className="flex items-center">
              <img src={nft.image} alt={nft.name} className="w-16 h-16 rounded-full mr-2" aria-label={nft.name} />
              <span>{nft.name} - Token ID: {nft.tokenId} - Owner: {nft.owner}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="w-full">
        <h2 className="text-xl font-bold mb-4">Transaction History</h2>
        <ul className="list-disc pl-4 mb-4">
          {transactionHistory.map((transaction) => (
            <li key={transaction} className="p-2 rounded-md mb-2">
              {transaction}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default UserDashboard;