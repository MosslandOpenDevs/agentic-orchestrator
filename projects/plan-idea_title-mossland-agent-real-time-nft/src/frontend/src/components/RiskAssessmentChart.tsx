import React, { useState, useEffect } from 'react';
import { Line } from 'react-svg-charts';
import { Chart as ChartJS, CategoryScale, Title, Legend } from 'chart.js';
import { LineChart, BarChart } from 'react-chartjs-2';
import { useMediaQuery } from 'react-use';

interface RiskAssessmentData {
  volatility: number;
  riskScore: number;
}

interface RiskAssessmentChartProps {
  data: RiskAssessmentData | null;
  isLoading: boolean;
  onError: (error: string) => void;
}

const RiskAssessmentChart: React.FC<RiskAssessmentChartProps> = ({ data, isLoading, onError }) => {
  const [chartData, setChartData] = useState<any | null>(null);
  const [chartError, setChartError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && data) {
      const chartData = {
        labels: ['Volatility'],
        datasets: [{
          label: 'Volatility',
          data: [data.volatility],
          backgroundColor: 'rgba(75,192,192,0.4)',
          borderColor: 'rgba(75,192,192,1)',
          borderWidth: 1
        }]
      };

      const riskScoreData = {
        labels: ['Risk Score'],
        datasets: [{
          label: 'Risk Score',
          data: [data.riskScore],
          backgroundColor: 'rgba(255,99,132,0.4)',
          borderColor: 'rgba(255,99,132,1)',
          borderWidth: 1
        }]
      };

      setChartData(chartData);
      setChartError(null);
    } else {
      setChartData(null);
      setChartError(null);
    }
  }, [isLoading, data]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (chartError) {
    return <div>Error: {chartError}</div>;
  }

  if (!chartData) {
    return <div>No data available.</div>;
  }

  const isSmallScreen = useMediaQuery({ maxWidth: 768 });

  return (
    <div className="bg-gray-100 p-6 rounded-lg shadow-md w-full" aria-label="Risk Assessment Chart">
      {isSmallScreen && (
        <div className="text-sm text-gray-600 font-italic">
          *Chart displayed for smaller screens.  Larger screens provide more detail.*
        </div>
      )}

      <p className="text-xl font-bold mb-4">Risk Assessment</p>

      {/* Volatility Chart */}
      <div className="mb-4">
        <LineChart
          data={chartData}
          width={isSmallScreen ? 300 : 600}
          height={isSmallScreen ? 200 : 400}
          options={{
            scales: {
              y: {
                beginAtZero: true
              }
            },
            plugins: {
              title: {
                display: true,
                text: 'Volatility'
              },
              legend: {
                display: false
              }
            }
          }}
        />
      </div>

      {/* Risk Score */}
      <div className="mb-4">
        <LineChart
          data={riskScoreData}
          width={isSmallScreen ? 300 : 600}
          height={isSmallScreen ? 200 : 400}
          options={{
            scales: {
              y: {
                beginAtZero: true
              }
            },
            plugins: {
              title: {
                display: true,
                text: 'Risk Score'
              },
              legend: {
                display: false
              }
            }
          }}
        />
      </div>
    </div>
  );
};

export default RiskAssessmentChart;