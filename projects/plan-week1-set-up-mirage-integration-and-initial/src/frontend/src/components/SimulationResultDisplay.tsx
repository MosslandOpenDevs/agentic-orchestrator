import React, { useState, useEffect } from 'react';

interface SimulationResult {
  id: string;
  name: string;
  outcome: string;
  confidenceLevel: number;
  detailedOutcomeVisualization: string; // Placeholder for actual visualization
  date: string;
}

interface SimulationResultDisplayProps {
  result: SimulationResult;
  isLoading: boolean;
  onError: (error: Error) => void;
}

const SimulationResultDisplay: React.FC<SimulationResultDisplayProps> = ({
  result,
  isLoading,
  onError,
} ) => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md text-center">
        <p className="text-lg font-semibold">Loading Simulation Result...</p>
      </div>
    );
  }

  if (onError) {
    return (
      <div className="bg-red-100 p-4 rounded shadow-md text-center">
        <p className="text-lg font-semibold">Error Loading Simulation Result</p>
        <p className="text-sm">Error: {result.error || 'Unknown error'}</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md text-center">
        <p className="text-lg font-semibold">No Simulation Result Found</p>
      </div>
    );
  }

  return (
    <div
      className="bg-white p-4 rounded shadow-md text-gray-800"
      aria-label={`Simulation Result for ${result.name}`}
      tabIndex={0}
    >
      <h2 className="text-xl font-semibold mb-4">{result.name}</h2>
      <p className="text-gray-700">Outcome: {result.outcome}</p>
      <p className="text-gray-700">Confidence Level: {result.confidenceLevel.toFixed(2)}%</p>
      <p className="text-gray-700">Date: {result.date}</p>

      {/* Detailed Outcome Visualization - Placeholder */}
      <div className="mt-6 rounded-xl shadow-md">
        <p className="text-lg font-semibold">Detailed Outcome Visualization</p>
        <img
          src={`https://via.placeholder.com/400x300?text=${result.outcome}`}
          alt={`Visualization for ${result.name}`}
          className="w-full h-48 object-cover rounded-md"
        />
      </div>
    </div>
  );
};

export default SimulationResultDisplay;