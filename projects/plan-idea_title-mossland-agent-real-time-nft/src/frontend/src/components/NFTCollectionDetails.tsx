import React, { useState, useEffect } from 'react';
import { Chart, ChartList, Line } from 'react-chartjs-2';
import axios from 'axios';

interface CollectionMetadata {
  name: string;
  symbol: string;
  description: string;
  image?: string;
  attributes?: any[];
  floorPrice?: number;
}

interface Transaction {
  date: string;
  price: number;
  tokenId: string;
  seller?: string;
}

interface NFTCollectionDetailsProps {
  collectionId: string;
}

const NFTCollectionDetails: React.FC<NFTCollectionDetailsProps> = ({ collectionId }) => {
  const [collectionData, setCollectionData] = useState<CollectionMetadata | null>(null);
  const [transactionHistory, setTransactionHistory] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCollectionData = async () => {
      try {
        const response = await axios.get<CollectionMetadata>(
          `https://ipfs.io/ipfs/QmN3xJ83y639Qe6jW2j6X2D8f969z66z4z98z` // Replace with actual IPFS link
        );
        setCollectionData(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load collection data.');
      } finally {
        setLoading(false);
      }
    };

    fetchCollectionData();
  }, [collectionId]);

  useEffect(() => {
    const fetchTransactionHistory = async () => {
      try {
        const response = await axios.get<Transaction[]>(
          `https://ipfs.io/ipfs/QmN3xJ83y639Qe6jW2j6X2D8f969z66z4z98z/transactions` // Replace with actual IPFS link
        );
        setTransactionHistory(response);
      } catch (err: any) {
        setError(err.message || 'Failed to load transaction history.');
      }
    };

    if (collectionData) {
      fetchTransactionHistory();
    }
  }, [collectionData]);

  const chartData = {
    labels: transactionHistory.map((tx) => tx.date),
    datasets: [
      {
        label: 'Price (USD)',
        data: transactionHistory.map((tx) => tx.price),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    scales: {
      x: {
        reverse: true,
      },
    },
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!collectionData) {
    return <div>No collection data found.</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md">
      <h1 className="text-3xl font-bold mb-4">{collectionData.name}</h1>
      <p className="text-gray-700 mb-4">{collectionData.description}</p>
      <img
        src={collectionData.image || '/default-nft.png'} // Replace with default image
        alt={collectionData.name}
        className="w-full h-48 object-cover rounded-md mb-4"
      />

      {collectionData.attributes && collectionData.attributes.length > 0 && (
        <div className="mb-4">
          <h2>Attributes</h2>
          {collectionData.attributes.map((attr) => (
            <div key={attr.name} className="flex items-center mb-2">
              <span className="text-gray-700">{attr.name}: {attr.value}</span>
            </div>
          ))}
        </div>
      )}

      {collectionData.floorPrice !== undefined && (
        <p className="text-xl font-semibold mb-4">Floor Price: ${collectionData.floorPrice}</p>
      )}

      {/* Price Chart */}
      <div className="max-w-full mx-auto">
        <Chart
          type="line"
          data={chartData}
          options={chartOptions}
          className="relative"
        />
      </div>

      {/* Transaction History */}
      <div className="mb-4">
        <h2>Transaction History</h2>
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left">
              <th>Date</th>
              <th>Price (USD)</th>
              <th>Token ID</th>
              <th>Seller</th>
            </tr>
          </thead>
          <tbody>
            {transactionHistory.map((tx) => (
              <tr key={tx.date} aria-label={`Transaction on ${tx.date}`}>
                <td className="text-left">{tx.date}</td>
                <td className="text-left">${tx.price.toFixed(2)}</td>
                <td className="text-left">{tx.tokenId}</td>
                <td className="text-left">{tx.seller || 'Unknown'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NFTCollectionDetails;