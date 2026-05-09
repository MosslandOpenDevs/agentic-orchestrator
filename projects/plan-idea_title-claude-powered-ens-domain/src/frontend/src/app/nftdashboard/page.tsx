import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/auth'; // Assuming Auth hook exists
import { NFT } from '../../types'; // Assuming NFT interface exists
import { getNFTs } from '../../api'; // Assuming API function exists

interface NFTDashboardProps {
  initialNFTs?: NFT[];
}

const NFTDashboard: React.FC<NFTDashboardProps> = ({ initialNFTs = [] }) => {
  const [nftList, setNftList] = useState<NFT[]>(initialNFTs);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    const fetchNFTs = async () => {
      try {
        const data = await getNFTs(user.address);
        setNftList(data);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch NFTs');
        setLoading(false);
      }
    };

    fetchNFTs();
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading NFTs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4">My NFTs</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {nftList.map((nft) => (
          <div
            key={nft.id}
            className="bg-white rounded-lg shadow-md hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`NFT: ${nft.name}`}
          >
            <img
              src={nft.image}
              alt={nft.name}
              className="w-full h-48 object-cover rounded-t-lg"
            />
            <div className="p-4">
              <h3 className="text-lg font-semibold mb-2">{nft.name}</h3>
              <p className="text-gray-600">Token ID: {nft.tokenId}</p>
              <p className="text-gray-600">Blockchain: {nft.blockchain}</p>
              <button
                onClick={() => router.push(`/nft-details/${nft.id}`)}
                className="mt-3 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                aria-label="View NFT Details"
              >
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NFTDashboard;