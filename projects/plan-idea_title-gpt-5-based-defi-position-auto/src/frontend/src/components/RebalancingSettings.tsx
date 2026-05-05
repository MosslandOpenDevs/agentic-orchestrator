import React, { useState, useEffect } from 'react';
import { Slider } from '@material-ui/core';
import { useMediaQuery } from 'react-use';

interface RebalancingSettingsProps {
  initialRiskTolerance?: number;
  initialAssetAllocation?: { [key: string]: number };
  initialGoal?: string;
  onRiskToleranceChange?: (riskTolerance: number) => void;
  onAssetAllocationChange?: (allocation: { [key: string]: number }) => void;
  onGoalChange?: (goal: string) => void;
}

const RebalancingSettings: React.FC<RebalancingSettingsProps> = ({
  initialRiskTolerance = 50,
  initialAssetAllocation = { 'Stocks': 50, 'Bonds': 30, 'Crypto': 20 },
  initialGoal = 'Retirement',
  onRiskToleranceChange,
  onAssetAllocationChange,
  onGoalChange,
}) => {
  const [riskTolerance, setRiskTolerance] = useState(initialRiskTolerance);
  const [assetAllocation, setAssetAllocation] = useState(initialAssetAllocation);
  const [goal, setGoal] = useState(initialGoal);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newRiskTolerance = parseInt(event.target.value, 10);
    setRiskTolerance(newRiskTolerance);
    if (onRiskToleranceChange) {
      onRiskToleranceChange(newRiskTolerance);
    }
  };

  const handleAssetAllocationChange = (newAllocation: { [key: string]: number }) => {
    setAssetAllocation(newAllocation);
    if (onAssetAllocationChange) {
      onAssetAllocationChange(newAllocation);
    }
  };

  const handleGoalChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newGoal = event.target.value;
    setGoal(newGoal);
    if (onGoalChange) {
      onGoalChange(newGoal);
    }
  };

  const isSmallScreen = useMediaQuery('(max-width: 600px)');

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full">
      {loading ? (
        <div className="text-center p-4">
          Loading settings...
        </div>
      ) : error ? (
        <div className="text-center p-4 text-red-500">
          Error: {error}
        </div>
      ) : (
        <>
          <h2 className="text-xl font-bold mb-4">Rebalancing Settings</h2>

          <div className="mb-4">
            <label className="block text-gray-700 font-semibold mb-2">Risk Tolerance</label>
            <Slider
              aria-label="Risk Tolerance"
              value={riskTolerance}
              onChange={handleRiskToleranceChange}
              defaultValue={initialRiskTolerance}
              min={0}
              max={100}
              className={`h-4 w-full bg-gray-300 rounded-full`}
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-semibold mb-2">Asset Allocation</label>
            <div className="flex items-center">
              <div className="flex-1 mr-2">Stocks</div>
              <input
                type="number"
                className="w-full h-4 bg-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={assetAllocation['Stocks']}
                onChange={(e) => handleAssetAllocationChange({ ...assetAllocation, 'Stocks': parseInt(e.target.value, 10) })}
              />
              <div className="flex-1 ml-2">Bonds</div>
              <input
                type="number"
                className="w-full h-4 bg-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={assetAllocation['Bonds']}
                onChange={(e) => handleAssetAllocationChange({ ...assetAllocation, 'Bonds': parseInt(e.target.value, 10) })}
              />
              <div className="flex-1 ml-2">Crypto</div>
              <input
                type="number"
                className="w-full h-4 bg-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={assetAllocation['Crypto']}
                onChange={(e) => handleAssetAllocationChange({ ...assetAllocation, 'Crypto': parseInt(e.target.value, 10) })}
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-semibold mb-2">Goal</label>
            <input
              type="text"
              className={`w-full h-4 bg-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 ${isSmallScreen ? 'max-w-xs' : ''}`}
              value={goal}
              onChange={handleGoalChange}
              aria-label="Set Investment Goal"
            />
          </div>
        </>
      )}
    </div>
  );
};

export default RebalancingSettings;