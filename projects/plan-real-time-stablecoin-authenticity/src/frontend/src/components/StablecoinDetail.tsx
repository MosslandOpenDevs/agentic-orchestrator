import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface StablecoinDetailProps {
  stablecoinId: string;
}

const StablecoinDetail: React.FC<StablecoinDetailProps> = ({ stablecoinId }) => {
  const {
    data,
    isLoading,
    error,
  } = useQuery(['stablecoinDetail', stablecoinId], async () => {
    // Simulate fetching data from an API
    const response = await fetch(`https://api.example.com/stablecoins/${stablecoinId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  const stablecoin = data;

  return (
    <div className="bg-white p-4 rounded-lg shadow-md w-full md:w-1/2">
      <h2 className="text-xl font-bold mb-4">{stablecoin.name}</h2>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Risk Score:</h3>
        <p className="text-gray-700">{stablecoin.riskScore}</p>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Stablecoin Details:</h3>
        <p className="text-gray-700">
          <strong>Symbol:</strong> {stablecoin.symbol}
        </p>
        <p className="text-gray-700">
          <strong>Decimals:</strong> {stablecoin.decimals}
        </p>
        <p className="text-gray-700">
          <strong>Circulating Supply:</strong> {stablecoin.circulatingSupply}
        </p>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Transaction History:</h3>
        {stablecoin.transactions.length > 0 ? (
          <ul className="list-disc text-gray-700 mb-0">
            {stablecoin.transactions.map((transaction) => (
              <li
                key={transaction.hash}
                aria-label={`Transaction: ${transaction.hash}`}
                className="hover:text-blue-500"
              >
                {transaction.date} - {transaction.amount} {transaction.currency}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-700">No transactions found.</p>
        )}
      </div>
    </div>
  );
};

export default StablecoinDetail;