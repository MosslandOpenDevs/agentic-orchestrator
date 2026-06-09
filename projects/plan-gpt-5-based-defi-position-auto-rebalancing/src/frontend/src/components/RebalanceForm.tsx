import React, { useState, useEffect } from 'react';

interface RiskTolerance {
  id: number;
  name: string;
  description: string;
}

interface RebalanceFormProps {
  riskTolerances: RiskTolerance[];
  onSubmit: (toleranceId: number) => void;
}

const RebalanceForm: React.FC<RebalanceFormProps> = ({ riskTolerances, onSubmit }) => {
  const [selectedTolerance, setSelectedTolerance] = useState<RiskTolerance | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(false);
    setError(null);
  }, [onSubmit]);

  const handleToleranceChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const selectedId = parseInt(event.target.value, 10);
    const tolerance = riskTolerances.find((t) => t.id === selectedId);

    setSelectedTolerance(tolerance);
  };

  const handleRebalanceClick = () => {
    if (!selectedTolerance) {
      setError('Please select a risk tolerance.');
      return;
    }

    setIsLoading(true);
    onSubmit(selectedTolerance.id);
  };

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md bg-white">
      <h2 className="text-xl font-semibold mb-4">Risk Tolerance Selection</h2>

      {error && <div className="text-red-500 p-2 rounded-md mb-4">{error}</div>}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Risk Tolerance:</label>
        <select
          id="riskTolerance"
          className="w-full px-3 py-2 rounded-md text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          onChange={handleToleranceChange}
          aria-label="Select Risk Tolerance"
          tabIndex={0}
        >
          <option value="" disabled>-- Select --</option>
          {riskTolerances.map((tolerance) => (
            <option key={tolerance.id} value={tolerance.id.toString()}>
              {tolerance.name} - {tolerance.description}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleRebalanceClick}
        className="w-full px-4 py-2 rounded-md bg-blue-500 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={isLoading}
        aria-label="Rebalance Portfolio"
      >
        {isLoading ? 'Rebalancing...' : 'Rebalance'}
      </button>
    </div>
  );
};

export default RebalanceForm;