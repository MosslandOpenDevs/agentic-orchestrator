import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface NFTFractionDetailsProps {
  fraction: {
    tokenId: string;
    fractionValue: number;
    ownershipPercentage: number;
    riskAssessment: string;
    transactionHistory: Array<string>;
  };
  isLoading: boolean;
  error?: string | null;
}

const NFTFractionDetails: React.FC<NFTFractionDetailsProps> = ({
  fraction,
  isLoading,
  error,
}) => {
  const router = useRouter();

  useEffect(() => {
    if (error) {
      router.push({
        pathname: router.pathname,
        state: { fromError: error },
      });
    }
  }, [router, error]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-gray-700">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex flex-col items-center">
        <div className="text-xl font-bold text-red-700">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col items-center">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">NFT Fraction Details</h1>
      <p className="text-gray-700 mb-4">Token ID: {fraction.tokenId}</p>
      <p className="text-xl font-semibold text-gray-800 mb-4">Fraction Value: ${fraction.fractionValue}</p>
      <p className="text-xl font-semibold text-gray-800 mb-4">Ownership Percentage: {fraction.ownershipPercentage}%</p>
      <p className="text-xl font-semibold text-gray-800 mb-4">Risk Assessment: {fraction.riskAssessment}</p>
      <div className="mt-4 w-full">
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Transaction History</h3>
        <ul className="list-disc list-inside text-gray-700">
          {fraction.transactionHistory.map((transaction, index) => (
            <li
              key={index}
              aria-label={`Transaction ${index + 1}`}
              className="mb-1"
            >
              {transaction}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default NFTFractionDetails;