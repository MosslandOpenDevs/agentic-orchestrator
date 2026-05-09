import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/router';

interface Asset {
  id: string;
  name: string;
  tokenId: string;
  contractAddress: string;
  tokenURI: string;
  mintDate: string;
  owner: string;
}

interface DomainDetailProps {
  domainName: string;
}

const DomainDetail: React.FC<DomainDetailProps> = ({ domainName }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const {
    data: domainData,
    isLoading,
    isError,
    refetch,
  } = useQuery<any, Error>({
    queryKey: ['domainDetail', domainName],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/domains/${domainName}`);

      if (!res.ok) {
        throw new Error(`Failed to fetch domain data: ${res.status}`);
      }

      return await res.json();
    },
  });

  useEffect(() => {
    if (isLoading) {
      setLoading(true);
    } else if (isError) {
      setError(isError.message);
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [isLoading, isError]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md text-center">
        <p>Loading domain details...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md text-center">
        <p>Error loading domain details: {error}</p>
        <button onClick={refetch} className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md">
          Refresh
        </button>
      </div>
    );
  }

  if (!domainData) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md text-center">
        <p>No domain data found.</p>
      </div>
    );
  }

  const { assets, mintingEnabled } = domainData;

  return (
    <div className="bg-white p-4 rounded-md shadow-md max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">{domainName}</h1>

      {/* Asset Management */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Assets</h2>
        {assets && assets.length > 0 ? (
          <ul className="list-disc pl-4 mb-2">
            {assets.map((asset) => (
              <li
                key={asset.id}
                aria-label={`Asset: ${asset.name}`}
                className="hover:text-blue-500"
              >
                {asset.name} - Token ID: {asset.tokenId} - Contract: {asset.contractAddress}
              </li>
            ))}
          </ul>
        ) : (
          <p>No assets found for this domain.</p>
        )}
      </div>

      {/* NFT Minting */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">NFT Minting</h2>
        {mintingEnabled ? (
          <p>NFT minting is enabled for this domain.</p>
        ) : (
          <p>NFT minting is currently disabled.</p>
        )}
      </div>

      <button
        onClick={refetch}
        className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-md mt-4"
        aria-label="Refresh Domain Data"
      >
        Refresh Data
      </button>
    </div>
  );
};

export default DomainDetail;