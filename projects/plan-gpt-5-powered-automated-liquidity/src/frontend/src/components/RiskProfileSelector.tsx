import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { useToast } from '@/components/ui/toast';

interface RiskProfileSelectorProps {
  initialRisk?: 'Conservative' | 'Moderate' | 'Aggressive';
  onRiskChange: (risk: 'Conservative' | 'Moderate' | 'Aggressive') => void;
}

const RiskProfileSelector: React.FC<RiskProfileSelectorProps> = ({ initialRisk, onRiskChange }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    // Simulate fetching risk profiles (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  const riskOptions = [
    { value: 'Conservative', label: 'Conservative' },
    { value: 'Moderate', label: 'Moderate' },
    { value: 'Aggressive', label: 'Aggressive' },
  ];

  const handleRiskChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedRisk = event.target.value;
    onRiskChange(selectedRisk);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <p>Loading risk profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-4">
        <Toast
          title={error}
          description={error}
          onClose={() => {}}
        />
      </div>
    );
  }

  return (
    <div className="mb-4 flex items-center justify-around w-full max-w-xs">
      <label className="text-sm font-medium leading-4 text-gray-900">Risk Profile</label>
      <Select
        onValueChange={handleRiskChange}
        defaultValue={initialRisk}
        placeholder="Select Risk Profile"
        className="w-full max-w-xs"
        aria-label="Select Risk Profile"
        required
        options={riskOptions}
        disabled={loading}
      />
    </div>
  );
};

export default RiskProfileSelector;