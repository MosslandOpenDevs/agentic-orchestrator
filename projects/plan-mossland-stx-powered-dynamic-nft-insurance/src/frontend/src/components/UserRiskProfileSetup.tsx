import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface RiskTolerance {
  id: number;
  name: string;
  description: string;
}

interface UserRiskProfileSetupProps {
  initialRisks: RiskTolerance[];
  onSubmit: (riskProfile: RiskTolerance | null) => void;
}

const UserRiskProfileSetup: React.FC<UserRiskProfileSetupProps> = ({ initialRisks, onSubmit }) => {
  const [selectedRisk, setSelectedRisk] = useState<RiskTolerance | null>(null);
  const [risks, setRisks] = useState<RiskTolerance[]>(initialRisks);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    if (selectedRisk) {
      onSubmit(selectedRisk);
    }
  }, [selectedRisk, onSubmit]);

  const handleRiskChange = (risk: RiskTolerance) => {
    setSelectedRisk(risk);
  };

  const handleConfirm = () => {
    setLoading(true);
    try {
      onSubmit(selectedRisk);
      toast('Risk profile updated successfully!', { type: 'success' });
    } catch (err) {
      setError(String(err));
      toast(String(err), { type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 rounded-lg shadow-md bg-white">
      <h2 className="text-xl font-semibold mb-4">Risk Profile Setup</h2>

      {error && (
        <div className="mt-2 p-2 rounded-md bg-red-100 border-red-500 text-red-600">
          {error}
        </div>
      )}

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Select your risk tolerance:
        </p>
        <div className="flex space-x-4">
          {risks.map((risk) => (
            <button
              key={risk.id}
              className={`
                px-4 py-2
                rounded-full
                bg-gray-200
                hover:bg-gray-300
                text-sm
                font-medium
                transition-colors
                duration-200
                ${selectedRisk && selectedRisk.id === risk.id ? 'bg-blue-500 hover:bg-blue-700' : ''}
                ${selectedRisk && selectedRisk.id === risk.id ? 'text-white' : 'text-gray-700'}
              `}
              aria-label={`Risk profile: ${risk.name}`}
              onClick={() => handleRiskChange(risk)}
              tabIndex={0}
            >
              {risk.name}
            </button>
          ))}
        </div>
      </div>

      <button
        className="mt-4
        bg-blue-500
        hover:bg-blue-700
        text-white
        font-bold
        px-4
        py-2
        rounded-full
        disabled
        opacity-50
        ${loading ? 'opacity-30' : ''}
        "
        onClick={handleConfirm}
        disabled={loading}
      >
        {loading ? 'Saving...' : 'Confirm Risk Profile'}
      </button>
    </div>
  );
};

export default UserRiskProfileSetup;