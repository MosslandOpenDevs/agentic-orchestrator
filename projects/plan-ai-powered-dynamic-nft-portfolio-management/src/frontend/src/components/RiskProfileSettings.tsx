import React, { useState, useEffect } from 'react';

interface RiskProfileSettingsProps {
  initialRiskLevel?: 'low' | 'medium' | 'high';
  onRiskLevelChange: (riskLevel: 'low' | 'medium' | 'high') => void;
}

const RiskProfileSettings: React.FC<RiskProfileSettingsProps> = ({
  initialRiskLevel = 'medium',
  onRiskLevelChange,
}) => {
  const [riskLevel, setRiskLevel] = useState<string>(initialRiskLevel);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    // Simulate fetching risk levels from an API or database
    setTimeout(() => {
      setIsLoading(false);
      // No actual error handling for this example, but could be added
    }, 500);
  }, []);

  const handleRiskLevelChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const newRiskLevel = event.target.value;
    setRiskLevel(newRiskLevel);
    onRiskLevelChange(newRiskLevel);
  };

  return (
    <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
      <h3 className="text-lg font-semibold mb-4">Risk Profile</h3>

      {isLoading && (
        <p className="text-gray-500 text-center">Loading...</p>
      )}

      {error && (
        <p className="text-red-500 text-center">Error: {error}</p>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Risk Level:</label>
        <select
          id="riskLevel"
          className="bg-gray-100 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 py-2 px-4"
          value={riskLevel}
          onChange={handleRiskLevelChange}
          aria-label="Select your risk level"
          tabIndex={0}
        >
          <option value="low" aria-label="Low Risk">Low Risk</option>
          <option value="medium" aria-label="Medium Risk">Medium Risk</option>
          <option value="high" aria-label="High Risk">High Risk</option>
        </select>
      </div>
    </div>
  );
};

export default RiskProfileSettings;