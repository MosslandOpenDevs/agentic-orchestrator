import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Gap } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import { use } from 'react';

Chart.register(...registerables);

interface AssetDetailsProps {
  assetId: string;
  assetName: string;
  price: number;
  volume: number;
  marketCap: number;
  tvl: number;
  isLoading: boolean;
  error?: string;
}

const AssetDetails: React.FC<AssetDetailsProps> = ({
  assetId,
  assetName,
  price,
  volume,
  marketCap,
  tvl,
  isLoading,
  error,
}) => {
  const [chartData, setChartData] = useState<any>();

  useEffect(() => {
    if (!isLoading && !error) {
      const data = {
        labels: [new Date(Date.now() - 60 * 60 * 1000), new Date(Date.now() - 120 * 60 * 1000), new Date(Date.now() - 180 * 60 * 1000), new Date(Date.now() - 240 * 60 * 1000)],
        datasets: [
          {
            label: 'Price (Last 4 Hours)',
            data: [price, price, price, price],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
          },
        ],
      };
      setChartData(data);
    }
  }, [isLoading, error]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Asset Details</h2>
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-100 p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Asset Details</h2>
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  const chartOptions = {
    scales: {
      y: {
        beginAtZero: true,
      },
      x: {
        display: true,
      },
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: function (data) {
            return data.parsed.toFixed(2);
          },
        },
      },
    },
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md w-full md:w-96">
      <h2 className="text-xl font-semibold mb-4">{assetName}</h2>
      <p className="text-gray-600 font-semibold">Asset ID: {assetId}</p>
      <div className="mb-4">
        <p className="text-xl font-bold">Price: ${price.toFixed(2)}</p>
        <p className="text-gray-600">Volume: ${volume} | Market Cap: ${marketCap} | TVL: ${tvl}</p>
      </div>
      <div className="relative">
        <LineChart
          data={chartData}
          options={chartOptions}
          width={400}
        />
      </div>
    </div>
  );
};

export default AssetDetails;