import React, { useState, useEffect } from 'react';

interface RiskProfile {
  id: string;
  name: 'Conservative' | 'Moderate' | 'Aggressive';
  description: string;
}

const RiskProfileSelector = ({
  riskProfiles: initialRiskProfiles,
  onRiskProfileChange,
}: {
  riskProfiles: RiskProfile[];
  onRiskProfileChange: (riskProfile: RiskProfile) => void;
}) => {
  const [riskProfiles, setRiskProfiles] = useState<RiskProfile[]>(initialRiskProfiles);
  const [selectedRiskProfile, setSelectedRiskProfile] = useState<RiskProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    // Simulate fetching risk profiles from an API
    setTimeout(() => {
      const fetchedRiskProfiles: RiskProfile[] = [
        { id: '1', name: 'Conservative', description: 'Low risk, low return' },
        { id: '2', name: 'Moderate', description: 'Balanced risk, balanced return' },
        { id: '3', name: 'Aggressive', description: 'High risk, high return' },
      ];
      setRiskProfiles(fetchedRiskProfiles);
      setIsLoading(false);
    }, 500);
  }, []);

  const handleRiskProfileChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = event.target.value;
    const selectedRiskProfile = riskProfiles.find((profile) => profile.id === selectedId);

    if (selectedRiskProfile) {
      setSelectedRiskProfile(selectedRiskProfile);
      onRiskProfileChange(selectedRiskProfile);
    } else {
      console.warn('Risk profile not found:', selectedId);
    }
  };

  if (isLoading) {
    return <div>Loading risk profiles...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!riskProfiles || riskProfiles.length === 0) {
    return <div>No risk profiles available.</div>;
  }

  return (
    <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
      <h3 className="text-lg font-semibold mb-4">Select Your Risk Profile</h3>
      <select
        id="risk-profile"
        className="bg-gray-200 hover:bg-gray-300 text-sm border-none focus:outline-none rounded-md py-2 px-4 w-full"
        aria-label="Risk Profile Selector"
        onChange={handleRiskProfileChange}
        tabIndex={0}
      >
        <option value="" disabled>Select a Risk Profile</option>
        {riskProfiles.map((profile) => (
          <option
            key={profile.id}
            value={profile.id}
            aria-label={`Risk Profile: ${profile.name}`}
          >
            {profile.name}
          </option>
        ))}
      </select>
      <p className="text-gray-700 mt-4">
        {selectedRiskProfile ? selectedRiskProfile.description : 'No risk profile selected.'}
      </p>
    </div>
  );
};

export default RiskProfileSelector;