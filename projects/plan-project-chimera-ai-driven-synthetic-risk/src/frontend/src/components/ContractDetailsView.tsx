import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface ContractDetails {
  codeHash: string;
  address: string;
  transactionHistory: Array<string>;
}

const ContractDetailsView = ({ contract }: ContractDetails) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md flex flex-col items-center">
        <p className="text-gray-700">Loading contract details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md flex flex-col items-center">
        <p className="text-gray-700">Error loading contract details: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-md shadow-md flex flex-col items-center">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Contract Details</h2>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Code Hash:</p>
        <p className="text-lg text-gray-800">{contract.codeHash}</p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Contract Address:</p>
        <p className="text-lg text-gray-800">{contract.address}</p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Transaction History:</p>
        <ul className="list-disc list-inside text-gray-700">
          {contract.transactionHistory.map((transaction, index) => (
            <li
              key={index}
              className="text-lg mb-1"
              aria-label={`Transaction ${index + 1}`}
            >
              {transaction}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ContractDetailsView;