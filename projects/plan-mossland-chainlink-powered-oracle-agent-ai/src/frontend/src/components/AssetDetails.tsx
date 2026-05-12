import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Chart, Line } from 'chart.js';

interface AssetDetailsProps {
  assetId: string;
}

interface AssetData {
  price: number;
  assetType: string;
  historicalData: { timestamps: string[]; prices: number }[];
}

const AssetDetails: React.FC<AssetDetailsProps> = ({ assetId }) => {
  const {
    data: assetData,
    isLoading,
    isError,
    error,
  } = useQuery<AssetData | null, Error>(['assetDetails', assetId], async () => {
    // Simulate fetching data from an API
    const response = await fetch(`https://api.example.com/assets/${assetId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  });

  if (isLoading) {
    return <div>Loading asset details...</div>;
  }

  if (isError) {
    return <div>Error fetching asset details: {error?.message}</div>;
  }

  if (!assetData) {
    return <div>Could not retrieve asset details.</div>;
  }

  const { price, assetType, historicalData } = assetData;

  const chartData = {
    labels: historicalData.map((dataPoint) => new Date(dataPoint.timestamps).toLocaleDateString()),
    datasets: [
      {
        label: 'Asset Price',
        data: historicalData.map((dataPoint) => dataPoint.prices),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    scales: {
      x: {
        type: 'datetime',
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Price'
        }
      }
    },
    plugins: {
      legend: {
        display: false
      }
    }
  };

  return (
    <div className="bg-gray-100 p-6 rounded-lg shadow-md w-full max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">{assetType} Details - Asset ID: {assetId}</h1>

      <div className="mb-4">
        <p className="text-gray-700">Price: <span className="font-bold text-xl">{price}</span></p>
      </div>

      <div className="flex flex-col md:flex-row">
        <div className="mb-4 md:mb-0 w-full">
          <p className="text-gray-700 mb-2">Historical Price Data:</p>
          <table className="table-auto w-full">
            <thead>
              <tr className="text-gray-800">
                <th>Timestamp</th>
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {historicalData.map((dataPoint) => (
                <tr key={dataPoint.timestamps} className="text-gray-700">
                  <td>{new Date(dataPoint.timestamps).toLocaleDateString()}</td>
                  <td>{dataPoint.prices}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="w-full">
          {/* Chart */}
          <canvas id="asset-price-chart" width={400} height={200} className="w-full h-full">
            <Line data={chartData} options={chartOptions} />
          </canvas>
        </div>
      </div>
    </div>
  );
};

export default AssetDetails;