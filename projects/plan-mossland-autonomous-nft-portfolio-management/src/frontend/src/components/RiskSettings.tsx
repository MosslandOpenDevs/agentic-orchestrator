import React, { useState, useEffect } from 'react';

interface RiskSettingsState {
  riskTolerance: number;
  timeHorizon: number;
}

interface RiskSettingsProps {
  initialRiskTolerance?: number;
  initialTimeHorizon?: number;
  onSaveSettings: (settings: RiskSettingsState) => void;
}

const RiskSettings: React.FC<RiskSettingsProps> = ({ initialRiskTolerance = 50, initialTimeHorizon = 5, onSaveSettings }) => {
  const [riskTolerance, setRiskTolerance] = useState<number>(initialRiskTolerance);
  const [timeHorizon, setTimeHorizon] = useState<number>(initialTimeHorizon);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate an API call to save settings
    setTimeout(() => {
      setIsLoading(false);
      // In a real application, you'd save the settings here
      // For demonstration purposes, we'll just log them
      console.log('Risk Settings Saved:', { riskTolerance, timeHorizon });
      onSaveSettings({ riskTolerance, timeHorizon });
    }, 1000);
  }, [onSaveSettings, riskTolerance, timeHorizon]);

  const handleRiskToleranceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value)) {
      setRiskTolerance(value);
    }
  };

  const handleTimeHorizonChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value)) {
      setTimeHorizon(value);
    }
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-4">Risk Settings</h2>

      {isLoading && (
        <div className="text-center mt-6 p-4 bg-gray-200 rounded-md">
          <p>Loading settings...</p>
        </div>
      )}

      {error && (
        <div className="text-center mt-6 p-4 bg-red-100 rounded-md shadow-red-500">
          <p className="text-red-600">Error: {error}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center mb-2">
          <label className="block text-gray-700 text-sm mb-2" htmlFor="riskTolerance">
            Risk Tolerance:
          </label>
          <input
            type="number"
            id="riskTolerance"
            className="w-full px-3 py-2 rounded-md border border-gray-300 text-gray-700 focus:outline-none focus:border-blue-200"
            value={riskTolerance}
            onChange={handleRiskToleranceChange}
            aria-label="Set your risk tolerance"
            tabIndex={0}
          />
        </div>

        <div className="flex items-center mb-2">
          <label className="block text-gray-700 text-sm mb-2" htmlFor="timeHorizon">
            Time Horizon:
          </label>
          <input
            type="number"
            id="timeHorizon"
            className="w-full px-3 py-2 rounded-md border border-gray-300 text-gray-700 focus:outline-none focus:border-blue-200"
            value={timeHorizon}
            onChange={handleTimeHorizonChange}
            aria-label="Set your time horizon"
            tabIndex={0}
          />
        </div>
      </div>

      <button
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full mt-4"
        onClick={() => {
          if (!riskTolerance || riskTolerance < 0 || riskTolerance > 100) {
            setError("Risk tolerance must be between 0 and 100");
            return;
          }
          if (!timeHorizon || timeHorizon < 0) {
            setError("Time horizon must be a positive number");
            return;
          }
          onSaveSettings({ riskTolerance, timeHorizon });
        }}
      >
        Save Settings
      </button>
    </div>
  );
};

export default RiskSettings;