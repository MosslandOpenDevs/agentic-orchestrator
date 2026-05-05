import React, { useState, useEffect } from 'react';
import { Slider } from '@material-ui/core';
import { useToast } from 'react-toastify';

interface RebalancingFormProps {
  initialRiskTolerance?: number;
  initialInvestmentHorizon?: number;
  onRebalance?: (riskTolerance: number, investmentHorizon: number) => void;
}

const RebalancingForm: React.FC<RebalancingFormProps> = ({
  initialRiskTolerance = 50,
  initialInvestmentHorizon = 5,
  onRebalance,
}) => {
  const [riskTolerance, setRiskTolerance] = useState(initialRiskTolerance);
  const [investmentHorizon, setInvestmentHorizon] = useState(initialInvestmentHorizon);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const riskToleranceOptions = [0, 100];
  const investmentHorizonOptions = [1, 5, 10, 20, 50];

  useEffect(() => {
    if (onRebalance && riskTolerance !== initialRiskTolerance && investmentHorizon !== initialInvestmentHorizon) {
      setIsLoading(true);
      try {
        onRebalance(riskTolerance, investmentHorizon);
        toast.success('Rebalancing successful!', {
          position: 'top-right',
          autoClose: 5000,
          style: {
            backgroundColor: '#4caf50',
            color: 'white',
            fontFamily: 'Roboto, sans-serif',
            fontSize: '16px',
            borderRadius: '5px',
            padding: '8px',
          },
        });
      } catch (err) {
        setError(String(err));
        toast.error('Rebalancing failed!', {
          position: 'top-right',
          autoClose: 5000,
          style: {
            backgroundColor: '#e57373',
            color: 'white',
            fontFamily: 'Roboto, sans-serif',
            fontSize: '16px',
            borderRadius: '5px',
            padding: '8px',
          },
        });
      } finally {
        setIsLoading(false);
      }
    }
  }, [onRebalance, riskTolerance, investmentHorizon, initialRiskTolerance, initialInvestmentHorizon]);

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRiskTolerance(parseInt(event.target.value, 10));
  };

  const handleInvestmentHorizonChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setInvestmentHorizon(parseInt(event.target.value, 10));
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-4">Rebalancing Form</h2>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Risk Tolerance</label>
        <Slider
          aria-label="Risk Tolerance"
          value={riskTolerance}
          defaultValue={initialRiskTolerance}
          min={0}
          max={100}
          onChange={handleRiskToleranceChange}
          className="w-full h-4 rounded-lg"
        />
      </div>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Investment Horizon</label>
        <select
          aria-label="Investment Horizon"
          value={investmentHorizon}
          onChange={handleInvestmentHorizonChange}
          className="w-full h-4 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {investmentHorizonOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={() => {
          if (isLoading) return;
          if (riskTolerance === undefined || investmentHorizon === undefined) return;
          if (onRebalance) {
            onRebalance(riskTolerance, investmentHorizon);
          }
        }}
        className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full max-w-md disabled:bg-blue-500 disabled:hover:bg-blue-700 disabled:text-gray-300`}
        disabled={isLoading}
      >
        {isLoading ? 'Rebalancing...' : 'Rebalance'}
      </button>

      {error && (
        <div className="mt-4 p-4 rounded-md bg-red-100 border-l-red-500 border-l-4">
          <p className="text-red-700 text-sm">Error: {error}</p>
        </div>
      )}
    </div>
  );
};

export default RebalancingForm;