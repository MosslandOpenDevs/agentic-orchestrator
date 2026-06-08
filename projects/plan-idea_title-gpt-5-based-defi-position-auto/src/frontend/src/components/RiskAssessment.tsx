import React, { useState, useEffect } from 'react';
import { Line } from 'react-svg-charts';
import { Chart } from 'chart.js/auto';

interface RiskAssessmentProps {
  initialPortfolio: {
    assets: { name: string; percentage: number }[];
  };
  riskTolerance: number;
  volatilityData: number[];
  stressTestData: number[];
}

const RiskAssessment: React.FC<RiskAssessmentProps> = ({
  initialPortfolio,
  riskTolerance,
  volatilityData,
  stressTestData,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adjustedRiskTolerance, setAdjustedRiskTolerance] = useState(riskTolerance);

  useEffect(() => {
    setLoading(true);
    try {
      // Simulate data fetching and processing
      // Replace with your actual data fetching logic
      const processedVolatility = volatilityData.map(v => v * (1 - Math.abs(adjustedRiskTolerance - 5) / 10));
      const processedStressTest = stressTestData.map(s => s * (1 - Math.abs(adjustedRiskTolerance - 5) / 10));

      setLoading(false);
    } catch (err) {
      setError(String(err));
      setLoading(false);
    }
  }, [adjustedRiskTolerance]);

  const handleRiskToleranceChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newRiskTolerance = parseInt(event.target.value, 10);
    if (!isNaN(newRiskTolerance)) {
      setAdjustedRiskTolerance(newRiskTolerance);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Risk Assessment</h2>

      <div className="flex flex-col md:flex-row mb-4">
        <div className="w-full md:w-1/2 mb-4">
          <p className="text-gray-700 mb-2">Portfolio Composition:</p>
          {initialPortfolio.assets.map((asset) => (
            <p key={asset.name} className="text-gray-700">{asset.name}: {asset.percentage}%</p>
          ))}
        </div>
        <div className="w-full md:w-1/2 mb-4">
          <label className="block text-gray-700 font-semibold mb-2">Risk Tolerance:</label>
          <input
            type="number"
            min="1"
            max="10"
            step="1"
            value={adjustedRiskTolerance}
            onChange={handleRiskToleranceChange}
            className="w-full p-2 border rounded-md shadow-sm"
            aria-label="Adjust Risk Tolerance"
            tabIndex={0}
          />
        </div>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 mb-2">Volatility Chart:</p>
        <Line
          data={{
            labels: volatilityData.map((_, index) => index),
            datasets: [
              {
                label: 'Volatility',
                data: processedVolatility,
                fill: false,
                backgroundColor: 'blue',
                borderColor: 'blue',
                borderWidth: 1,
              },
            ],
          }}
          width={400}
          height={200}
          className="mt-2"
        />
      </div>

      <div className="mb-4">
        <p className="text-gray-700 mb-2">Stress Test Simulation:</p>
        <Line
          data={{
            labels: stressTestData.map((_, index) => index),
            datasets: [
              {
                label: 'Stress Test Loss',
                data: processedStressTest,
                fill: false,
                backgroundColor: 'red',
                borderColor: 'red',
                borderWidth: 1,
              },
            ],
          }}
          width={400}
          height={200}
          className="mt-2"
        />
      </div>
    </div>
  );
};

export default RiskAssessment;