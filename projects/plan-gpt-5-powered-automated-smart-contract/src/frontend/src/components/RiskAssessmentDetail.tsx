import React, { useState, useEffect } from 'react';

interface RiskAssessmentDetailProps {
  riskAssessment: {
    riskScore: number;
    riskFactors: string[];
    assessmentTimestamp: string;
    id?: string; // Optional ID for potential fetching
  };
  isLoading: boolean;
  error?: string | null;
}

const RiskAssessmentDetail: React.FC<RiskAssessmentDetailProps> = ({
  riskAssessment,
  isLoading,
  error,
}) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow">
        <div className="text-center">Loading Risk Assessment...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded shadow">
        <div className="text-center text-red-700">Error: {error}</div>
      </div>
    );
  }

  if (!riskAssessment) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow">
        <div className="text-center">No risk assessment data available.</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded shadow w-full md:w-1/2 lg:w-1/3">
      <h2 className="text-xl font-bold mb-4">Risk Assessment Detail</h2>
      <p className="text-gray-700 mb-2">Risk Score: {riskAssessment.riskScore}</p>
      <ul className="space-y-2 mb-4">
        {riskAssessment.riskFactors.map((factor, index) => (
          <li
            key={index}
            className="text-gray-700"
            aria-label={`Risk factor ${index + 1}: ${factor}`}
          >
            {factor}
          </li>
        ))}
      </ul>
      <p className="text-gray-700 mb-2">Assessment Timestamp: {riskAssessment.assessmentTimestamp}</p>
    </div>
  );
};

export default RiskAssessmentDetail;