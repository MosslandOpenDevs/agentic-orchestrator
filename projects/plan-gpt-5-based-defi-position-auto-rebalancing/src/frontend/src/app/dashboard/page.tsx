import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart } from 'chart.js';

interface PortfolioData {
  assets: {
    [key: string]: {
      name: string;
      quantity: number;
      price: number;
    };
  };
  riskScore: number;
  rebalancingRecommendations: string[];
  nftPositions: {
    [key: string]: {
      name: string;
      quantity: number;
      price: number;
      nftId: string;
    };
  };
}

interface DashboardProps {
  data?: PortfolioData;
  isLoading?: boolean;
  error?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ data, isLoading, error }) => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (data) {
      setChartData(data);
    }
  }, [data]);

  const chartDataConfig: ChartConfiguration = {
    type: 'pie',
    data: {
      labels: Object.keys(data?.assets),
      datasets: [{
        label: 'Portfolio Value',
        data: Object.values(data?.assets).map(asset => asset.quantity * asset.price),
        backgroundColor: ['#4CAF50', '#FF9800', '#f44336', '#2196F3', '#00BCD4'],
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
        },
      },
    },
  };

  const ChartData: ChartConfiguration = chartDataConfig;

  if (isLoading) {
    return <div>Loading Dashboard...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data) {
    return <div>No data available.</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex">
      <div className="w-1/2 p-4">
        <h1 className="text-2xl font-bold mb-4">Portfolio Overview</h1>
        <p className="text-gray-700 mb-4">Risk Score: {data.riskScore}</p>
        <p className="text-gray-700 mb-4">Rebalancing Recommendations: {data.rebalancingRecommendations.join(', ')}</p>
        <h2 className="text-xl font-bold mb-4">NFT Positions</h2>
        {Object.entries(data.nftPositions).map(([nftId, nft]) => (
          <div key={nftId} className="mb-2 p-2 border-gray-300 rounded-md">
            <p className="font-semibold mb-1">NFT: {nft.name} (ID: {nft.nftId})</p>
            <p className="text-gray-700">Quantity: {nft.quantity}</p>
            <p className="text-gray-700">Price: ${nft.price}</p>
          </div>
        ))}
      </div>

      <div className="w-1/2 p-4">
        <h2 className="text-xl font-bold mb-4">Portfolio Visualization</h2>
        {chartData && (
          <canvas id="portfolioChart" width="400" height="200"></canvas>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

interface ChartConfiguration {
  type: 'pie';
  data: {
    labels: string[];
    datasets: any[];
  };
  options: any;
}