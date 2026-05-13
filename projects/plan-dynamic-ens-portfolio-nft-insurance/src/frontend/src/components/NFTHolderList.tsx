import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFTHolder {
  address: string;
  name: string;
  balance: number;
}

interface NFTHolderListProps {
  initialData?: NFTHolder[];
  loading?: boolean;
  error?: string;
}

const NFTHolderList: React.FC<NFTHolderListProps> = ({ initialData = [], loading = false, error }) => {
  const [searchParams] = useSearchParams();
  const filter = searchParams.get('filter') || '';
  const sort = searchParams.get('sort') || 'name';

  const [data, setData] = useState<NFTHolder[]>(initialData);
  const [isLoading, setIsLoading] = useState(loading);
  const [errorState, setErrorState] = useState<string | null>(error);

  useEffect(() => {
    if (searchParams.get('filter')) {
      // Placeholder for filtering logic - Replace with actual filtering
      // Example:
      // const filteredData = data.filter(holder => holder.name.toLowerCase().includes(searchParams.get('filter')!.toLowerCase()));
      // setData(filteredData);
    }
  }, [searchParams]);

  useEffect(() => {
    if (sort === 'balance') {
      // Placeholder for sorting logic - Replace with actual sorting
      // Example:
      // data.sort((a, b) => b.balance - a.balance);
    } else {
      // Ensure data is sorted by name if sort is not balance
      if (data.length > 0) {
        data.sort((a, b) => {
          if (a.name < b.name) return -1;
          if (a.name > b.name) return 1;
          return 0;
        });
      }
    }
    setData(data);
  }, [sort]);

  if (isLoading) {
    return <div>Loading NFT Holders...</div>;
  }

  if (errorState) {
    return <div>Error: {errorState}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">NFT Holders</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {data.map((holder) => (
          <div
            key={holder.address}
            className="bg-gray-100 p-4 rounded-md shadow-md hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`NFT Holder: ${holder.address}`}
          >
            <p className="text-lg font-semibold mb-2">
              {holder.name}
            </p>
            <p className="text-gray-700">
              Address: {holder.address}
            </p>
            <p className="text-gray-700">
              Balance: {holder.balance}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NFTHolderList;