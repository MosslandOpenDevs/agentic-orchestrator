import React, { useState, useEffect } from 'react';

interface RiskAssessment {
  vulnerability: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  recommendations: string[];
}

interface RiskAssessmentDetailsProps {
  riskAssessment: RiskAssessment | null;
  isLoading: boolean;
  error?: string;
}

const RiskAssessmentDetails: React.FC<RiskAssessmentDetailsProps> = ({
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
    <div className="bg-white p-4 rounded shadow w-full max-w-md">
      <h2 className="text-xl font-bold mb-4">Risk Assessment Details</h2>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Vulnerability:</p>
        <p className="text-gray-900">{riskAssessment.vulnerability}</p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Severity:</p>
        <p className="text-xl font-bold">{riskAssessment.severity}</p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Mitigation Recommendations:</p>
        <ul className="list-disc text-gray-700">
          {riskAssessment.recommendations.map((recommendation, index) => (
            <li
              key={index}
              className="text-gray-900"
              aria-label={`Recommendation ${index + 1}: ${recommendation}`}
            >
              {recommendation}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default RiskAssessmentDetails;