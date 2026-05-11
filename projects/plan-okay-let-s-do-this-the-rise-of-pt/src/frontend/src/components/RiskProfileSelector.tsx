import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';

interface RiskProfileSelectorProps {
  onRiskProfileChange: (riskProfile: 'Conservative' | 'Moderate' | 'Aggressive') => void;
}

const RiskProfileSelector: React.FC<RiskProfileSelectorProps> = ({ onRiskProfileChange }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null | undefined>(null);
  const { toast } = useToast();

  const riskProfiles = ['Conservative', 'Moderate', 'Aggressive'] as const;
  const selectedRiskProfile = riskProfiles[0]; // Default to Conservative

  useEffect(() => {
    // Simulate an API call to fetch risk profiles (replace with actual API call)
    const fetchData = async () => {
      setLoading(true);
      try {
        // Replace this with your actual API call
        // await someApiCall();
        // setError(null);
      } catch (e) {
        setError('Failed to load risk profiles.');
        toast({
          title: 'Error',
          description: 'Failed to load risk profiles.',
          status: 'error',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleRiskProfileChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOption = event.target.value;
    onRiskProfileChange(selectedOption);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-xs">
      <label className="text-sm font-medium mb-2" htmlFor="risk-profile">
        Select Risk Profile
      </label>
      <Select
        id="risk-profile"
        className="w-full max-w-xs"
        defaultValue={selectedRiskProfile}
        onValueChange={handleRiskProfileChange}
        options={riskProfiles}
        aria-label="Select Risk Profile"
        placeholder="Select Risk Profile"
        disabled={loading}
      >
        {loading && <Button className="w-full max-w-xs" disabled>Loading...</Button>}
      </Select>
      {error && (
        <div className="text-red-500 p-2">
          {error}
        </div>
      )}
    </div>
  );
};

export default RiskProfileSelector;