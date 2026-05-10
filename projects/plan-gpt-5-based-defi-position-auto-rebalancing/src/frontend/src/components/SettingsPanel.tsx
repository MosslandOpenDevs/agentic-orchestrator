import React, { useState, useEffect } from 'react';

interface SettingsPanelProps {
  initialRiskTolerance?: 'low' | 'medium' | 'high';
  initialAggressivenessLevel?: number;
  onRiskToleranceChange: (riskTolerance: 'low' | 'medium' | 'high') => void;
  onAggressivenessLevelChange: (aggressivenessLevel: number) => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
  initialRiskTolerance = 'medium',
  initialAggressivenessLevel = 5,
  onRiskToleranceChange,
  onAggressivenessLevelChange,
}) => {
  const riskToleranceOptions = ['low', 'medium', 'high'] as const;
  const [riskTolerance, setRiskTolerance] = useState<string>(initialRiskTolerance);
  const [aggressivenessLevel, setAggressivenessLevel] = useState<number>(initialAggressivenessLevel);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching settings data (replace with actual API call)
    setTimeout(() => {
      setIsLoading(false);
    }, 500);
  }, []);

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setRiskTolerance(event.target.value);
    onRiskToleranceChange(event.target.value);
  };

  const handleAggressivenessLevelChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const level = parseInt(event.target.value, 10);
    if (!isNaN(level)) {
      setAggressivenessLevel(level);
      onAggressivenessLevelChange(level);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow">
        <div className="text-center">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded shadow">
        <div className="text-red-600">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded shadow w-full max-w-md">
      <h2 className="text-lg font-semibold mb-4">Portfolio Settings</h2>

      <div className="mb-4">
        <label className="block text-gray-700 font-medium mb-2">Risk Tolerance</label>
        <select
          className="bg-gray-200 hover:bg-gray-300 text-gray-700 border border-gray-300 rounded py-2 px-4"
          value={riskTolerance}
          onChange={handleRiskToleranceChange}
          aria-label="Select Risk Tolerance"
          tabIndex={0}
        >
          {riskToleranceOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4">
        <label className="block text-gray-700 font-medium mb-2">Aggressiveness Level</label>
        <input
          type="number"
          className="bg-gray-200 hover:bg-gray-300 text-gray-700 border border-gray-300 rounded py-2 px-4"
          value={aggressivenessLevel.toString()}
          onChange={handleAggressivenessLevelChange}
          min="1"
          max="10"
          aria-label="Enter Aggressiveness Level"
          tabIndex={0}
        />
      </div>
    </div>
  );
};

export default SettingsPanel;