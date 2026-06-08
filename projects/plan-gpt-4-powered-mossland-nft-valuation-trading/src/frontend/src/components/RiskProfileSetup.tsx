import React, { useState, useEffect } from 'react';
import { useMediaQuery } from 'next/useMeta';

interface RiskProfileSetupProps {
  initialRisk?: 'low' | 'medium' | 'high';
  onRiskChange: (risk: 'low' | 'medium' | 'high') => void;
}

const RiskProfileSetup: React.FC<RiskProfileSetupProps> = ({ initialRisk, onRiskChange }) => {
  const [risk, setRisk] = useState<string | undefined>(initialRisk);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  const isSmallScreen = useMediaQuery('(max-width: 768px)');

  useEffect(() => {
    // Simulate fetching risk data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
      // Example data - replace with your actual data
      const riskData = ['low', 'medium', 'high'];
      if (initialRisk) {
        setRisk(initialRisk);
      }
    }, 500);
  }, [initialRisk]);

  const handleRiskChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newRisk = event.target.value;
    setRisk(newRisk);
    onRiskChange(newRisk);
  };

  return (
    <div className="bg-white p-4 rounded-md shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-4">Risk Profile Setup</h2>

      {loading && (
        <div className="text-center mt-4">
          <p>Loading risk profile data...</p>
        </div>
      )}

      {error && (
        <div className="text-red-500 text-center mt-4">
          <p>Error: {error}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Risk Tolerance:</label>
          <select
            className={`bg-gray-100 hover:bg-gray-200 text-gray-700 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 p-2 ${isSmallScreen ? 'w-full max-w-300' : 'w-full'}  `}
            value={risk}
            onChange={handleRiskChange}
            aria-label="Select your risk tolerance"
            tabIndex={0}
          >
            <option value="low" disabled>Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
        </div>
      )}
    </div>
  );
};

export default RiskProfileSetup;