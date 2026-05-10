import React, { useState, useEffect } from 'react';

interface RiskScoreCardProps {
  score: number;
  confidenceLevel: number;
  contractAddress: string;
  contractName: string;
  totalSupply: number;
  isLoading: boolean;
  onError: (error: string) => void;
}

const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  score,
  confidenceLevel,
  contractAddress,
  contractName,
  totalSupply,
  isLoading,
  onError,
}) => {
  const [details, setDetails] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !details) {
      // Simulate fetching details (replace with actual API call)
      setTimeout(() => {
        setDetails({
          name: contractName,
          address: contractAddress,
          totalSupply: totalSupply,
        });
      }, 500);
    }
  }, [isLoading, details]);

  useEffect(() => {
    if (error) {
      setError(error);
    } else {
      setError(null);
    }
  }, [error]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-6 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold">Risk Score</div>
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-6 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-red-600">Error</div>
        <div className="text-gray-600">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-6 rounded-lg shadow-md flex flex-col items-center">
      <div className="text-xl font-bold">Risk Score: {score}</div>
      <div className="text-gray-600">
        Confidence Level: {confidenceLevel}%
      </div>
      <div className="text-gray-600 mt-4">
        Contract Details:
        <div className="mt-2">
          <span className="font-semibold">Name:</span> {contractName}
        </div>
        <div className="mt-2">
          <span className="font-semibold">Address:</span> {contractAddress}
        </div>
        <div className="mt-2">
          <span className="font-semibold">Total Supply:</span> {totalSupply}
        </div>
      </div>
    </div>
  );
};

export default RiskScoreCard;