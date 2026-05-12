import React, { useState, useEffect } from 'react';
import { useSession } from 'next-session';

interface RiskProfile {
  id: string;
  name: string;
  description: string;
}

interface SettingsState {
  riskProfile: RiskProfile | null;
  returnTarget: number | null;
  isLoading: boolean;
  error: string | null;
}

const Settings = ({ riskProfiles }: { riskProfiles: RiskProfile[] }) => {
  const { session } = useSession();
  const [settingsState: SettingsState] = useState({
    riskProfile: null,
    returnTarget: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    // Simulate fetching settings data
    const fetchData = async () => {
      try {
        // Replace with actual API call
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay
        const data = {
          riskProfile: {
            id: 'low',
            name: 'Conservative',
            description: 'Low risk portfolio',
          },
          returnTarget: 5,
        };
        settingsState.riskProfile = data.riskProfile;
        settingsState.returnTarget = data.returnTarget;
        settingsState.isLoading = false;
      } catch (error) {
        settingsState.error = 'Failed to load settings.';
        settingsState.isLoading = false;
      }
    };

    fetchData();
  }, []);

  const handleRiskProfileChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    settingsState.riskProfile = riskProfiles.find(
      (rp) => rp.id === event.target.value
    );
  };

  const handleReturnTargetChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(event.target.value, 10);
    if (!isNaN(value)) {
      settingsState.returnTarget = value;
    } else {
      settingsState.returnTarget = null;
    }
  };

  if (settingsState.isLoading) {
    return <div>Loading settings...</div>;
  }

  if (settingsState.error) {
    return <div>Error: {settingsState.error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-4">Portfolio Settings</h2>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Risk Profile:</label>
        <select
          id="riskProfile"
          className="w-full px-3 py-2 border rounded-md text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={settingsState.riskProfile ? settingsState.riskProfile.name : null}
          onChange={handleRiskProfileChange}
          aria-label="Select Risk Profile"
          tabIndex={0}
        >
          <option value="" disabled>Select a Risk Profile</option>
          {riskProfiles.map((rp) => (
            <option key={rp.id} value={rp.id}>
              {rp.name}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Return Target (%):</label>
        <input
          type="number"
          id="returnTarget"
          className="w-full px-3 py-2 border rounded-md text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={settingsState.returnTarget ? settingsState.returnTarget.toString() : ''}
          onChange={handleReturnTargetChange}
          aria-label="Enter Return Target"
          tabIndex={0}
        />
      </div>

      <button
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
        onClick={() => {
          // Simulate saving settings
          console.log('Saving settings:', settingsState);
        }}
      >
        Save Settings
      </button>
    </div>
  );
};

export default Settings;