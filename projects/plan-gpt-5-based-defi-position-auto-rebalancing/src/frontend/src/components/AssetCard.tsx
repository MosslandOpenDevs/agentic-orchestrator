import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Gap } from 'react-chartjs-2';
import { Chart, CategoryScale } from 'chart.js';

interface AssetCardProps {
  assetName: string;
  currentPrice: number;
  quantityHeld: number;
  id: string; // Unique identifier for the asset
  isLoading?: boolean;
  error?: string;
  onAssetChange?: (assetId: string) => void; // Callback for external updates
}

const AssetCard: React.FC<AssetCardProps> = ({
  assetName,
  currentPrice,
  quantityHeld,
  id,
  isLoading = false,
  error,
  onAssetChange,
}) => {
  const [chartData, setChartData] = useState<ChartData>({
    labels: [],
    datasets: [],
  });

  useEffect(() => {
    // Simulate fetching data for the chart. Replace with actual API call.
    const fetchData = async () => {
      const mockData = [
        { date: '2023-01-01', price: currentPrice * 0.98 },
        { date: '2023-01-08', price: currentPrice * 1.01 },
        { date: '2023-01-15', price: currentPrice * 1.02 },
        { date: '2023-01-22', price: currentPrice * 0.99 },
        { date: '2023-01-29', price: currentPrice * 1.03 },
      ];

      setChartData({
        labels: mockData.map((item) => item.date),
        datasets: [
          {
            label: 'Price',
            data: mockData.map((item) => item.price),
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
          },
        ],
      });
    };

    fetchData();
  }, [currentPrice]);

  const chartOptions = {
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
          text: 'Price',
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div
      className="bg-white rounded-lg shadow-md overflow-hidden flex flex-col w-full"
      aria-label={`Asset Card for ${assetName}`}
      tabIndex={0}
    >
      {isLoading && <p className="text-gray-300 p-4">Loading...</p>}
      {error && <p className="text-red-500 p-4">{error}</p>}
      <div className="p-4">
        <h3 className="text-xl font-semibold text-gray-800">{assetName}</h3>
        <p className="text-gray-600">Current Price: ${currentPrice.toFixed(2)}</p>
        <p className="text-gray-600">Quantity Held: {quantityHeld}</p>
      </div>

      <div className="relative flex-grow">
        <LineChart
          data={chartData}
          options={chartOptions}
          width={360}
          height={180}
        >
          <Line
            curveTangent={true}
            borderColor="rgb(75, 192, 192)"
            borderWidth={2}
          />
          <XAxis dataKey="date" tickLineTop={false} tickLineBottom={false} />
          <YAxis dataKey="price" />
          <Tooltip />
        </LineChart>
      </div>

      {onAssetChange && (
        <button
          onClick={() => onAssetChange(id)}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
          aria-label={`Update ${assetName}`}
        >
          Update Asset
        </button>
      )}
    </div>
  );
};

interface ChartData {
  labels: string[];
  datasets: any[];
}

export default AssetCard;