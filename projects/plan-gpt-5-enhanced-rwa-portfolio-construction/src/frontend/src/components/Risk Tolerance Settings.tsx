import React, { useState, useEffect } from 'react';

interface RiskToleranceSettingsProps {
  initialRiskLevel?: 'low' | 'medium' | 'high';
  onRiskLevelChange: (riskLevel: 'low' | 'medium' | 'high') => void;
}

const RiskToleranceSettings: React.FC<RiskToleranceSettingsProps> = ({
  initialRiskLevel = 'medium',
  onRiskLevelChange,
}) => {
  const [riskLevel, setRiskLevel] = useState<string>(initialRiskLevel);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    // Simulate fetching risk level data (replace with actual API call)
    setTimeout(() => {
      setIsLoading(false);
      // No actual data fetching needed for this example, just simulating loading
    }, 500);
  }, []);

  const handleRiskLevelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newRiskLevel = event.target.value;
    setRiskLevel(newRiskLevel);
    onRiskLevelChange(newRiskLevel);
  };

  return (
    <div className="bg-gray-100 p-6 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-4">Risk Tolerance Settings</h2>

      {isLoading && (
        <p className="text-gray-500 text-center">Loading...</p>
      )}

      {error && (
        <p className="text-red-500 text-center">Error: {error}</p>
      )}

      <div className="mb-4">
        <label className="block text-gray-700 font-medium mb-2">Select Risk Level:</label>
        <select
          id="riskLevel"
          className="bg-white border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500 text-gray-800 sm:text-sm"
          value={riskLevel}
          onChange={handleRiskLevelChange}
          aria-label="Select your risk tolerance level"
          tabIndex={0}
        >
          <option value="low" key="low">
            Low Risk
          </option>
          <option value="medium" key="medium">
            Medium Risk
          </option>
          <option value="high" key="high">
            High Risk
          </option>
        </select>
      </div>

      <p className="text-gray-700 mb-4">
        Risk levels represent the potential for investment gains and losses.
        <br />
        <b>Low Risk:</b>  Prioritizes capital preservation with minimal potential for growth. Suitable for investors with a short time horizon and low risk tolerance.
        <br />
        <b>Medium Risk:</b>  Balances potential growth with moderate risk. Suitable for investors with a medium time horizon and moderate risk tolerance.
        <br />
        <b>High Risk:</b>  Aims for maximum growth potential but involves significant risk of loss. Suitable for investors with a long time horizon and high risk tolerance.
      </p>
    </div>
  );
};

export default RiskToleranceSettings;