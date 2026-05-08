import React, { useState, useEffect } from 'react';

interface RiskAssessmentDetailsProps {
  gpt5Output: string;
  rebalancingRecommendations: string;
  isLoading: boolean;
  error?: string;
}

const RiskAssessmentDetails: React.FC<RiskAssessmentDetailsProps> = ({
  gpt5Output,
  rebalancingRecommendations,
  isLoading,
  error,
}) => {
  const [assessmentDetails, setAssessmentDetails] = useState<string>('');

  useEffect(() => {
    if (!isLoading && !error) {
      setAssessmentDetails(`${gpt5Output}\n\nRebalancing Recommendations: ${rebalancingRecommendations}`);
    }
  }, [gpt5Output, rebalancingRecommendations, isLoading, error]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-center">
          <p>Loading Risk Assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-center">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
      <h2 className="text-xl font-bold mb-4">Risk Assessment Details</h2>
      <p className="text-gray-700">
        {assessmentDetails}
      </p>
    </div>
  );
};

export default RiskAssessmentDetails;