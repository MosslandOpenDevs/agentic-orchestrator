import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';

interface FractionDetailsData {
  tokenId: string;
  fractionId: string;
  owner: string;
  fractionPercentage: number;
  price: number;
  riskAssessment: string;
  transactionHistory: Array<string>;
}

interface FractionDetailsProps {
  fractionData: FractionDetailsData;
  isLoading: boolean;
  isError: boolean;
  onClose: () => void;
}

const FractionDetails: React.FC<FractionDetailsProps> = ({
  fractionData,
  isLoading,
  isError,
  onClose,
}) => {
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isError) {
      router.push('/'); // Navigate back to home on error
    }
  }, [isLoading, isError, router]);

  if (isLoading) {
    return (
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">Loading...</h2>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4">
        <h2 className="text-xl font-semibold mb-4">Error Loading Data</h2>
        <p className="text-gray-600">
          Failed to fetch fraction details. Please try again later.
        </p>
      </div>
    );
  }

  return (
    <div
      className="max-w-4xl mx-auto p-4 rounded-lg shadow-md overflow-hidden"
      aria-label="NFT Fraction Details"
    >
      {fractionData && (
        <>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">{fractionData.tokenId}</h2>
            <button onClick={onClose} aria-label="Close">
              <ArrowLeft className="h-6 w-6" />
            </button>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Fraction ID:</p>
            <p className="text-lg">{fractionData.fractionId}</p>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Owner:</p>
            <p className="text-lg text-green-500">{fractionData.owner}</p>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Fraction Percentage:</p>
            <p className="text-lg">{fractionData.fractionPercentage}%</p>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Price:</p>
            <p className="text-lg">${fractionData.price}</p>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Risk Assessment:</p>
            <p className="text-lg">{fractionData.riskAssessment}</p>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 font-medium">Transaction History:</p>
            <ul className="list-disc list-inside text-sm">
              {fractionData.transactionHistory.map((transaction, index) => (
                <li key={index} className="mb-1">
                  {transaction}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default FractionDetails;