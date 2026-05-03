import React, { useState, useEffect } from 'react';

interface TransactionDetailsProps {
  transaction: TransactionData;
  isLoading: boolean;
  error?: string | null;
}

interface TransactionData {
  transactionHash: string;
  blockNumber: number;
  timestamp: string;
  senderAddress: string;
  recipientAddress: string;
  value: number;
}

const TransactionDetails: React.FC<TransactionDetailsProps> = ({
  transaction,
  isLoading,
  error,
}) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return <div>Loading transaction details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!transaction) {
    return <div>No transaction data available.</div>;
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6 md:p-8 lg:p-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">
        Transaction Details
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p className="text-gray-700 mb-2">Transaction Hash:</p>
          <p className="text-xl font-semibold">{transaction.transactionHash}</p>
        </div>

        <div>
          <p className="text-gray-700 mb-2">Block Number:</p>
          <p className="text-xl font-semibold">{transaction.blockNumber}</p>
        </div>

        <div>
          <p className="text-gray-700 mb-2">Timestamp:</p>
          <p className="text-xl font-semibold">{transaction.timestamp}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p className="text-gray-700 mb-2">Sender Address:</p>
          <p className="text-xl font-semibold">{transaction.senderAddress}</p>
        </div>

        <div>
          <p className="text-gray-700 mb-2">Recipient Address:</p>
          <p className="text-xl font-semibold">{transaction.recipientAddress}</p>
        </div>

        <div>
          <p className="text-gray-700 mb-2">Transaction Value:</p>
          <p className="text-xl font-semibold">
            {transaction.value} {transaction.value > 0 ? 'ETH' : 'BTC'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetails;