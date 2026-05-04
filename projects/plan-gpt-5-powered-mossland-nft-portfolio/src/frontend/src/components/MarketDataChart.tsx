import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart, defaults } from 'chart.js';

interface MarketDataChartProps {
  asset: string;
  timeframe: '1m' | '5m' | '1h' | '3h' | '6h' | '12h' | '1d' | '3d' | '7d';
  data: { labels: string[]; values: number[] } | null;
  isLoading: boolean;
  error?: string;
}

const MarketDataChart: React.FC<MarketDataChartProps> = ({
  asset,
  timeframe,
  data,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return <div>Loading data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data) {
    return <div>No data available.</div>;
  }

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: `${asset} Price`,
        data: data.values,
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: timeframe,
        },
      },
      y: {
        beginAtZero: true,
        display: true,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
    onClick: (event, element, datasetIndex, dataIndex) => {
      // Handle click events here if needed
    },
    tooltips: {
      enabled: true,
    },
    animation: {
      duration: 0,
    },
  };

  defaults.global.animation = false;
  Chart.register(Line);

  return (
    <div
      className="flex flex-col w-full max-w-full"
      aria-label={`Market Data Chart for ${asset}`}
      tabIndex={0}
    >
      <Line data={chartData} options={chartOptions} />
    </div>
  );
};

export default MarketDataChart;