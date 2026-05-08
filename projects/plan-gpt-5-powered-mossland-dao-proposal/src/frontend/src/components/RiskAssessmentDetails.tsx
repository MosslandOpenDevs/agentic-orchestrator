import React, { useState, useEffect } from 'react';

interface RiskAssessmentDetailsProps {
  data?: {
    standardDeviation?: number;
    riskFactors?: string[];
    rebalancingRecommendations?: string[];
  };
  isLoading?: boolean;
  error?: string;
}

const RiskAssessmentDetails: React.FC<RiskAssessmentDetailsProps> = ({
  data,
  isLoading = false,
  error,
}) => {
  const [details, setDetails] = useState<any>(null);

  useEffect(() => {
    if (data) {
      setDetails(data);
    }
  }, [data]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md flex items-center justify-center">
        Loading risk assessment details...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded shadow-md flex items-center justify-center">
        Error loading risk assessment details: {error}
      </div>
    );
  }

  if (!details) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md flex items-center justify-center">
        No risk assessment details available.
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded shadow-md flex flex-col items-center">
      <h2 className="text-xl font-semibold mb-4">Risk Assessment Details</h2>

      <div className="mb-4">
        <p className="text-gray-700">Standard Deviation: {details.standardDeviation || 'N/A'}</p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Risk Factors:</p>
        <ul className="list-disc pl-4">
          {details.riskFactors &&
            details.riskFactors.map((factor, index) => (
              <li key={index} aria-label={`Risk factor ${index + 1}: ${factor}`}>
                {factor}
              </li>
            ))}
        </ul>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Rebalancing Recommendations:</p>
        <ul className="list-disc pl-4">
          {details.rebalancingRecommendations &&
            details.rebalancingRecommendations.map((recommendation, index) => (
              <li key={index} aria-label={`Rebalancing recommendation ${index + 1}: ${recommendation}`}>
                {recommendation}
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
};

export default RiskAssessmentDetails;