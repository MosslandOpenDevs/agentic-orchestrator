import React, { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';
import { useDebounce } from 'use-lodash-debounce';

Chart.register(...registerables);

interface RiskScoreChartProps {
  data: { stablecoin: string; timeSeries: number[] }[];
  initialStablecoin?: string;
}

const RiskScoreChart: React.FC<RiskScoreChartProps> = ({ data, initialStablecoin }) => {
  const [selectedStablecoin, setSelectedStablecoin] = useState<string | undefined>(initialStablecoin);
  const [chartData, setChartData] = useState<any>();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLCanvasElement>(null);

  const filteredData = data.filter((item) =>
    item.stablecoin.toLowerCase().includes(selectedStablecoin?.toLowerCase() || '')
  );

  const options = {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    plugins: {
      title: {
        display: true,
        text: selectedStablecoin ? `Risk Score for ${selectedStablecoin}` : 'Risk Score Chart',
      },
    },
  };

  const handleStablecoinChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newStablecoin = event.target.value;
    setSelectedStablecoin(newStablecoin);
  };

  useEffect(() => {
    if (filteredData.length === 0) {
      setChartData(null);
      return;
    }

    const labels = filteredData.map((item) => item.timeSeries.map((_, index) => `${index}`));
    const dataPoints = filteredData.map((item) => item.timeSeries);

    setChartData({
      labels,
      datasets: [
        {
          label: selectedStablecoin || 'Risk Score',
          data: dataPoints.flatMap(arr => arr),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
          tension: 0.4,
        },
      ],
    });
    setLoading(false);
  }, [filteredData, selectedStablecoin]);

  useEffect(() => {
    if (chartData) {
      if (chartRef.current) {
        const ctx = chartRef.current.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, chartRef.current.width, chartRef.current.height);
          new Line(ctx, {
            data: chartData,
            options: options,
          });
        }
      }
    }
  }, [chartData]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="flex flex-col w-full max-w-full">
      <div className="mb-4 flex items-center space-x-3">
        <label className="text-sm font-medium">Stablecoin:</label>
        <input
          type="text"
          className="px-3 py-2 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={selectedStablecoin}
          onChange={handleStablecoinChange}
          aria-label="Filter stablecoins"
        />
      </div>
      <div className="relative">
        <canvas ref={chartRef} className="w-full h-56 mx-auto" aria-label="Risk Score Chart"></canvas>
      </div>
    </div>
  );
};

export default RiskScoreChart;