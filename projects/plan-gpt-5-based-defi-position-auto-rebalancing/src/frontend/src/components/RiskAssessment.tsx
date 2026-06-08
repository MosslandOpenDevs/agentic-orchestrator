import React, { useState, useEffect } from 'react';
import { Line } from 'react-svg-charts';
import { Chart } from 'chart.js/auto';

interface RiskAssessmentProps {
  initialRisk: number;
  volatilityData: { [key: string]: number } | null;
  lossScenarioData: { [key: string]: number } | null;
  isLoading: boolean;
  error?: string;
}

const RiskAssessment: React.FC<RiskAssessmentProps> = ({
  initialRisk,
  volatilityData,
  lossScenarioData,
  isLoading,
  error,
}) => {
  const [risk, setRisk] = useState(initialRisk);
  const [lossScenario, setLossScenario] = useState(0);

  useEffect(() => {
    if (volatilityData && lossScenarioData) {
      // Simulate data processing - replace with actual logic
      const volatility = Math.random() * 100;
      const scenario = Math.random() * 500;
      setRisk(volatility);
      setLossScenario(scenario);
    }
  }, [volatilityData, lossScenarioData]);

  if (isLoading) {
    return <div>Loading Risk Assessment...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const volatilityChartData = {
    labels: ['Low', 'Medium', 'High'],
    datasets: [
      {
        label: 'Volatility',
        data: [risk, risk + 20, risk + 40],
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
        ],
        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)'],
        borderWidth: 1,
      },
    ],
  };

  const lossScenarioData = {
    labels: ['Low', 'Medium', 'High'],
    datasets: [
      {
        label: 'Potential Loss',
        data: [lossScenario, lossScenario + 100, lossScenario + 200],
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
        ],
        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(255, 206, 86, 1)'],
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-bold mb-4">Risk Assessment</h2>

      <div className="mb-4">
        <p className="text-gray-700">
          Current Risk Level: {risk.toFixed(2)}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-md shadow-sm p-4">
          <h3 className="text-lg font-semibold mb-2">Volatility Chart</h3>
          <Line
            data={volatilityChartData}
            width={300}
            height={200}
            className="mt-4"
          />
        </div>

        <div className="bg-white rounded-md shadow-sm p-4">
          <h3 className="text-lg font-semibold mb-2">Loss Scenario Simulation</h3>
          <Line
            data={lossScenarioData}
            width={300}
            height={200}
            className="mt-4"
          />
        </div>
      </div>
    </div>
  );
};

export default RiskAssessment;