import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface NFTPositionDetailsProps {
  nftId: string;
  positionData: any; // Replace 'any' with a specific interface for positionData
}

const NFTPositionDetails: React.FC<NFTPositionDetailsProps> = ({ nftId, positionData }) => {
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id') || nftId;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (id !== nftId) {
      // Simulate fetching data based on ID - replace with actual API call
      setTimeout(() => {
        setLoading(false);
        setError(null);
      }, 500);
    }
  }, [id, nftId]);

  if (loading) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-md text-gray-700">
        <div className="text-center mb-4">
          <p className="text-xl font-semibold">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-md text-gray-700">
        <div className="text-center mb-4">
          <p className="text-xl font-semibold">Error: {error.message}</p>
        </div>
      </div>
    );
  }

  const { nftDetails, defiPositionDetails, riskAssessment, rebalancingRecommendations } = positionData;

  return (
    <div className="bg-white p-4 rounded-lg shadow-md text-gray-700">
      {nftDetails && (
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">NFT Details</h2>
          <p className="text-gray-700">Name: {nftDetails.name}</p>
          <p className="text-gray-700">Token ID: {nftDetails.tokenId}</p>
          <p className="text-gray-700">Image URL: {nftDetails.imageUrl}</p>
        </div>
      )}

      {defiPositionDetails && (
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">DeFi Position Details</h2>
          <p className="text-gray-700">LP Token: {defiPositionDetails.lpToken}</p>
          <p className="text-gray-700">Amount: {defiPositionDetails.amount}</p>
        </div>
      )}

      {riskAssessment && (
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Risk Assessment</h2>
          <p className="text-gray-700">Risk Level: {riskAssessment.riskLevel}</p>
          <p className="text-gray-700">Description: {riskAssessment.description}</p>
        </div>
      )}

      {rebalancingRecommendations && (
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Rebalancing Recommendations</h2>
          <p className="text-gray-700">Recommendation: {rebalancingRecommendations.recommendation}</p>
        </div>
      )}
    </div>
  );
};

export default NFTPositionDetails;