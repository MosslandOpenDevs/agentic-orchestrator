import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js';
import { use } from 'react';

interface PortfolioSimulationData {
  date: string;
  value: number;
}

interface SimulationResultsProps {
  data: PortfolioSimulationData[];
  scenario?: string;
  riskMetrics?: {
    volatility: number;
    sharpeRatio: number;
  };
}

const SimulationResultsComponent: React.FC<SimulationResultsProps> = ({ data, scenario, riskMetrics }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!data || data.length === 0) {
      setLoading(false);
      setError(new Error('No simulation data available.'));
      return;
    }

    setLoading(false);
  }, [data]);

  const chartData = {
    labels: data.map(item => item.date),
    datasets: [
      {
        label: 'Portfolio Value',
        data: data.map(item => item.value),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: scenario || 'Portfolio Simulation',
      },
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Value',
        },
      },
    },
  };

  if (loading) {
    return <div>Loading simulation results...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      {riskMetrics && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">Risk Metrics</h3>
          <p className="text-gray-700">Volatility: {riskMetrics.volatility.toFixed(2)}</p>
          <p className="text-gray-700">Sharpe Ratio: {riskMetrics.sharpeRatio.toFixed(2)}</p>
        </div>
      )}
      <ResponsiveContainer height={400}>
        <LineChart
          data={chartData}
          options={chartOptions}
          width={600}
        >
          <Line />
          <XAxis />
          <YAxis />
          <Tooltip />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SimulationResultsComponent;