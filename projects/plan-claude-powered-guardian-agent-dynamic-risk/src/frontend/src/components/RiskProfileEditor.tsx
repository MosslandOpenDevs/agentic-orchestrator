import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface RiskProfile {
  riskTolerance: 'Conservative' | 'Moderate' | 'Aggressive';
  volatilityThreshold: number;
  assetAllocation: {
    stocks: number;
    bonds: number;
    cash: number;
  };
}

interface RiskProfileEditorProps {
  initialRiskProfile?: Partial<RiskProfile>;
}

const RiskProfileEditor: React.FC<RiskProfileEditorProps> = ({ initialRiskProfile = {} }) => {
  const [riskProfile, setRiskProfile] = useState<RiskProfile>(initialRiskProfile);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setRiskProfile((prev) => ({ ...prev, riskTolerance: event.target.value }));
  };

  const handleVolatilityThresholdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value);
    setRiskProfile((prev) => ({ ...prev, volatilityThreshold: isNaN(value) ? 0 : value }));
  };

  const handleAssetAllocationChange = (
    event: React.ChangeEvent<HTMLInputElement>,
    assetType: 'stocks' | 'bonds' | 'cash'
  ) => {
    const value = parseFloat(event.target.value);
    setRiskProfile((prev) => ({
      ...prev,
      assetAllocation: {
        ...prev.assetAllocation,
        [assetType]: isNaN(value) ? 0 : value,
      },
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast.success('Risk profile updated successfully!', {
        position: 'top-right',
        autoClose: 5000,
        theme: 'colored',
      });
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      toast.error(err.message, {
        position: 'top-right',
        autoClose: 5000,
        theme: 'colored',
      });
      setLoading(false);
    }
  };

  useEffect(() => {
    // You might want to perform validation here based on the riskProfile state
  }, [riskProfile]);

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded-lg shadow-md">
      <form onSubmit={handleSubmit} aria-label="Risk Profile Editor">
        <h2 className="text-lg font-semibold mb-4">Risk Profile Configuration</h2>

        {/* Risk Tolerance Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700">Risk Tolerance:</label>
          <select
            className="mt-1 block w-full sm:max-w-300 px-4 py-2 rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            value={riskProfile.riskTolerance}
            onChange={handleRiskToleranceChange}
            aria-label="Select Risk Tolerance"
          >
            <option value="Conservative">Conservative</option>
            <option value="Moderate">Moderate</option>
            <option value="Aggressive">Aggressive</option>
          </select>
        </div>

        {/* Volatility Threshold Adjustment */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700">Volatility Threshold:</label>
          <input
            type="number"
            className="mt-1 block w-full sm:max-w-300 px-4 py-2 rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            value={riskProfile.volatilityThreshold}
            onChange={handleVolatilityThresholdChange}
            aria-label="Enter Volatility Threshold"
            placeholder="Enter value"
          />
        </div>

        {/* Asset Allocation Customization */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700">Asset Allocation:</label>
          <div className="flex flex-col sm:flex-row">
            <div className="mb-2 sm:mb-0">
              <label className="block text-sm font-medium text-gray-700">Stocks:</label>
              <input
                type="number"
                className="mt-1 block w-full sm:max-w-100 px-4 py-2 rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
                value={riskProfile.assetAllocation.stocks}
                onChange={(event) => handleAssetAllocationChange(event, 'stocks')}
                aria-label="Enter Stock Allocation"
                placeholder="Enter percentage"
              />
            </div>
            <div className="mr-2 sm:mr-0">
              <label className="block text-sm font-medium text-gray-700">Bonds:</label>
              <input
                type="number"
                className="mt-1 block w-full sm:max-w-100 px-4 py-2 rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
                value={riskProfile.assetAllocation.bonds}
                onChange={(event) => handleAssetAllocationChange(event, 'bonds')}
                aria-label="Enter Bond Allocation"
                placeholder="Enter percentage"
              />
            </div>
            <div className="mr-2 sm:mr-0">
              <label className="block text-sm font-medium text-gray-700">Cash:</label>
              <input
                type="number"
                className="mt-1 block w-full sm:max-w-100 px-4 py-2 rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
                value={riskProfile.assetAllocation.cash}
                onChange={(event) => handleAssetAllocationChange(event, 'cash')}
                aria-label="Enter Cash Allocation"
                placeholder="Enter percentage"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-md w-full sm:w-auto"
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save Risk Profile'}
        </button>
      </form>
    </div>
  );
};

export default RiskProfileEditor;