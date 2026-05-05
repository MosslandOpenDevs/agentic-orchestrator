import React, { useState, useEffect } from 'react';
import { LineChart, BarChart, XAxis, YAxis, Tooltip, Cell } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import { use } from 'react';

Chart.register(...registerables);

interface SecurityDetailsProps {
  tokenSymbol: string;
  data: {
    priceChart: {
      labels: string[];
      data: number[];
    };
    historicalData: {
      dates: string[];
      prices: number[];
    };
    riskMetrics: {
      volatility: number;
      liquidity: number;
      beta: number;
    };
  };
}

const SecurityDetails: React.FC<SecurityDetailsProps> = ({ tokenSymbol, data }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) {
      setLoading(false);
      setError('No data available.');
      return;
    }

    setLoading(false);
  }, [data]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md w-full animate-fadein">
        <div className="text-center">Loading security details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md w-full animate-fadein">
        <div className="text-red-700 text-xl">Error: {error}</div>
      </div>
    );
  }

  const options = {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-4xl mx-auto animate-fadein">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">
        {tokenSymbol} Security Details
      </h1>

      {/* Price Chart */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Price Chart</h2>
        <LineChart data={data.priceChart} options={options} width={400} />
      </div>

      {/* Historical Data */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Historical Data</h2>
        <table className="table table-striped">
          <thead>
            <tr>
              <th>Date</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {data.historicalData.dates.map((date, index) => (
              <tr key={index}>
                <td>{date}</td>
                <td>{data.historicalData.prices[index].toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Risk Metrics */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-700 mb-2">Risk Metrics</h2>
        <p className="text-gray-700">
          Volatility: {data.riskMetrics.volatility.toFixed(2)}
        </p>
        <p className="text-gray-700">
          Liquidity: {data.riskMetrics.liquidity.toFixed(2)}
        </p>
        <p className="text-gray-700">
          Beta: {data.riskMetrics.beta.toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export default SecurityDetails;