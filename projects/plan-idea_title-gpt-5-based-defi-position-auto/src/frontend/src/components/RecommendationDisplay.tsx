import React, { useState, useEffect } from 'react';

interface RecommendationDisplayProps {
  recommendation: {
    text: string;
    rationale: string;
    timestamp?: number;
  } | null;
  isLoading: boolean;
  onError: (error: string) => void;
}

const RecommendationDisplay: React.FC<RecommendationDisplayProps> = ({
  recommendation,
  isLoading,
  onError,
}) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md text-center">
        <p className="text-gray-700">Loading recommendation...</p>
      </div>
    );
  }

  if (recommendation === null) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md text-center">
        <p className="text-gray-700">No recommendation available.</p>
      </div>
    );
  }

  if (!isMounted) {
    return null;
  }

  const errorMessage = recommendation.text;

  return (
    <div
      className="bg-white p-4 rounded shadow-md overflow-hidden text-gray-800"
      aria-label="GPT-5 Recommendation"
      role="alert"
    >
      {recommendation.text && (
        <p className="mb-2 font-semibold">Recommendation:</p>
        <p className="text-lg">{recommendation.text}</p>
      )}

      {recommendation.rationale && (
        <p className="mb-2 font-semibold">Rationale:</p>
        <p className="text-gray-700">{recommendation.rationale}</p>
      )}

      {errorMessage && (
        <div className="mt-4 border-red-500 p-2 rounded text-red-500">
          Error: {errorMessage}
        </div>
      )}
    </div>
  );
};

export default RecommendationDisplay;