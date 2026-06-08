import React, { useState, useEffect } from 'react';
import { Line } from 'react-svg-charts';
import { Chart } from 'chart.js/auto';

interface RiskAssessmentProps {
  riskData: {
    volatility: number;
    lossTolerance: number;
    scenarios: {
      conservative: {
        lossPercentage: number;
        probability: number;
      };
      moderate: {
        lossPercentage: number;
        probability: number;
      };
      aggressive: {
        lossPercentage: number;
        probability: number;
      };
    };
  };
  isLoading: boolean;
  error: string | null;
}

const RiskAssessment: React.FC<RiskAssessmentProps> = ({
  riskData,
  isLoading,
  error,
}) => {
  const [chartData, setChartData] = useState<any>();

  useEffect(() => {
    if (!riskData || isLoading) return;

    const data = {
      labels: ['Conservative', 'Moderate', 'Aggressive'],
      datasets: [
        {
          label: 'Loss Percentage',
          data: [riskData.scenarios.conservative.lossPercentage, riskData.scenarios.moderate.lossPercentage, riskData.scenarios.aggressive.lossPercentage],
          backgroundColor: [
            'rgba(255, 99, 132, 0.2)',
            'rgba(54, 162, 235, 0.2)',
            'rgba(255, 206, 86, 0.2)',
          ],
          borderColor: [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };

    setChartData(data);
  }, [riskData]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      <h2 className="text-xl font-bold mb-4">Risk Assessment</h2>

      {/* Volatility Chart */}
      <div className="mb-4">
        <Line
          data={chartData}
          width={300}
          height={200}
          xAccessor={(d) => d.label}
          yAccessor={(d) => d.data[0]}
          className="chart-container"
        />
      </div>

      {/* Loss Tolerance Indicator */}
      <div className="mb-4">
        <p className="text-lg font-semibold">Loss Tolerance:</p>
        <div className="flex items-center">
          <span className="text-xs text-green-500 mr-2">{riskData.lossTolerance}</span>
          <p className="text-gray-600">units</p>
        </div>
      </div>

      {/* Scenario Analysis */}
      <div className="mb-4">
        <h3 className="text-lg font-bold mb-2">Scenario Analysis</h3>
        <table className="min-w-0 table-auto">
          <thead>
            <tr>
              <th className="text-left px-2">Scenario</th>
              <th className="text-left px-2">Loss Percentage</th>
              <th className="text-left px-2">Probability</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="text-left px-2">Conservative</td>
              <td className="text-left px-2">{riskData.scenarios.conservative.lossPercentage}%</td>
              <td className="text-left px-2">{riskData.scenarios.conservative.probability}</td>
            </tr>
            <tr>
              <td className="text-left px-2">Moderate</td>
              <td className="text-left px-2">{riskData.scenarios.moderate.lossPercentage}%</td>
              <td className="text-left px-2">{riskData.scenarios.moderate.probability}</td>
            </tr>
            <tr>
              <td className="text-left px-2">Aggressive</td>
              <td className="text-left px-2">{riskData.scenarios.aggressive.lossPercentage}%</td>
              <td className="text-left px-2">{riskData.scenarios.aggressive.probability}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RiskAssessment;