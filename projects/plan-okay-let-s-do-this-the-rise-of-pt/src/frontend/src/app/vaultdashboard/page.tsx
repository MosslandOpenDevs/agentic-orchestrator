import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface VaultData {
  balance: number;
  riskProfile: 'low' | 'medium' | 'high';
  manualAdjustment: number;
}

interface VaultDashboardProps {
  initialVaultData?: Partial<VaultData>;
}

const VaultDashboard: React.FC<VaultDashboardProps> = ({ initialVaultData = {} }) => {
  const [vaultData, setVaultData] = useState<VaultData>({
    balance: 0,
    riskProfile: 'medium',
    manualAdjustment: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: VaultData = {
          balance: 10000,
          riskProfile: 'high',
          manualAdjustment: 500,
        };
        setVaultData(data);
        setIsLoading(false);
      } catch (err) {
        setError('Failed to fetch vault data.');
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleRiskProfileChange = (profile: 'low' | 'medium' | 'high') => {
    setVaultData((prev) => ({ ...prev, riskProfile: profile }));
  };

  const handleManualAdjustmentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(event.target.value, 10);
    setVaultData((prev) => ({ ...prev, manualAdjustment: isNaN(value) ? 0 : value }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading vault data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-2xl font-bold mb-4">Vault Dashboard</h2>

      <div className="mb-4">
        <p className="text-gray-700 mb-2">Balance: ${vaultData.balance}</p>
        <div className="flex items-center space-x-3">
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => handleRiskProfileChange('low')}
            aria-label="Select Low Risk Profile"
          >
            Low
          </button>
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => handleRiskProfileChange('medium')}
            aria-label="Select Medium Risk Profile"
          >
            Medium
          </button>
          <button
            className="bg-blue-500 hover:bg-blue-700 text-white py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => handleRiskProfileChange('high')}
            aria-label="Select High Risk Profile"
          >
            High
          </button>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 mb-2">Manual Adjustment:</p>
        <input
          type="number"
          className="bg-gray-200 py-2 px-3 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-full max-w-sm"
          value={vaultData.manualAdjustment.toString()}
          onChange={handleManualAdjustmentChange}
          aria-label="Enter manual adjustment value"
        />
      </div>

      <button className="bg-green-500 hover:bg-green-700 text-white py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 w-full max-w-sm"
              onClick={() => router.push('/')}
              >
        Return to Home
      </button>
    </div>
  );
};

export default VaultDashboard;