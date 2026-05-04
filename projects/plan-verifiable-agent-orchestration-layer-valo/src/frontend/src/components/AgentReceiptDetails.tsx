import React, { useState, useEffect } from 'react';

interface AgentReceiptDetailsProps {
  receiptId: string;
  agentId: string;
  amount: number;
  currency: string;
  timestamp: string;
  verificationStatus?: 'pending' | 'verified' | 'failed';
  isLoading?: boolean;
  error?: string;
}

const AgentReceiptDetails: React.FC<AgentReceiptDetailsProps> = ({
  receiptId,
  agentId,
  amount,
  currency,
  timestamp,
  verificationStatus,
  isLoading = false,
  error,
}) => {
  const [details, setDetails] = useState<any>({});

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    const fetchData = async () => {
      try {
        const response = await new Promise((resolve) =>
          setTimeout(() => {
            resolve({
              receiptId,
              agentId,
              amount,
              currency,
              timestamp,
              verificationStatus,
            });
          }, 1000)
        );
        setDetails(response);
      } catch (err) {
        console.error('Error fetching data:', err);
        setDetails({});
        if (error) {
          setDetails({ error });
        }
      }
    };

    if (!isLoading) {
      fetchData();
    }
  }, [receiptId, agentId, amount, currency, timestamp, verificationStatus, isLoading]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md overflow-hidden w-full md:w-96">
      {isLoading && (
        <div className="text-center p-4">
          Loading Agent Receipt Details...
        </div>
      )}
      {error && (
        <div className="text-red-500 p-4 text-center">
          Error: {error}
        </div>
      )}

      {details && (
        <div className="p-4">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Agent Receipt Details
          </h2>
          <p className="text-gray-700 mb-4">
            Receipt ID: {receiptId}
          </p>
          <p className="text-gray-700 mb-4">
            Agent ID: {agentId}
          </p>
          <p className="text-gray-700 mb-4">
            Amount: {amount} {currency}
          </p>
          <p className="text-gray-700 mb-4">
            Timestamp: {timestamp}
          </p>
          <p className="text-gray-700 mb-4">
            Verification Status: {verificationStatus || 'N/A'}
          </p>
        </div>
      )}
    </div>
  );
};

export default AgentReceiptDetails;