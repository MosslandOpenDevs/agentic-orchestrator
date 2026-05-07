import React, { useState, useEffect } from 'react';

interface RiskAssessmentDetailProps {
  riskAssessment: {
    riskFactors: string[];
    overallRiskScore: number;
    assessmentTimestamp: string;
  };
  isLoading: boolean;
  error?: string;
}

const RiskAssessmentDetail: React.FC<RiskAssessmentDetailProps> = ({
  riskAssessment,
  isLoading,
  error,
}) => {
  const [ariaLabel, setAriaLabel] = useState('Risk Assessment Detail');

  useEffect(() => {
    setAriaLabel(`Risk Assessment Detail: ${riskAssessment.overallRiskScore}`);
  }, [riskAssessment.overallRiskScore]);

  if (isLoading) {
    return (
      <div
        aria-label={ariaLabel}
        className="bg-gray-100 p-6 rounded-lg shadow-md flex flex-col items-center"
      >
        <div className="text-center font-bold text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        aria-label={ariaLabel}
        className="bg-red-100 p-6 rounded-lg shadow-md flex flex-col items-center"
      >
        <div className="text-center font-bold text-xl text-red-600">
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div
      aria-label={ariaLabel}
      className="bg-gray-100 p-6 rounded-lg shadow-md flex flex-col items-center"
    >
      <h2 className="text-2xl font-bold mb-4">Risk Assessment Details</h2>
      <p className="text-gray-700 mb-4">
        Risk Factors: {riskAssessment.riskFactors.join(', ')}
      </p>
      <p className="text-3xl font-bold mb-4">Overall Risk Score: {riskAssessment.overallRiskScore}</p>
      <p className="text-gray-700 mb-4">
        Assessment Timestamp: {riskAssessment.assessmentTimestamp}
      </p>
    </div>
  );
};

export default RiskAssessmentDetail;