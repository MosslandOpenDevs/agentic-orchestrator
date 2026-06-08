import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart } from 'chart.js';

interface NFTPosition {
  tokenId: string;
  quantity: number;
  price: number;
}

interface RiskAssessment {
  overallRisk: number;
  riskCategories: {
    high: number;
    medium: number;
    low: number;
  };
}

interface RebalancingRecommendation {
  asset: string;
  percentage: number;
}

interface DashboardProps {
  nftPositions: NFTPosition[];
  riskAssessment: RiskAssessment;
  rebalancingRecommendations: RebalancingRecommendation[];
}

const Dashboard: React.FC<DashboardProps> = ({ nftPositions, riskAssessment, rebalancingRecommendations }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (nftPositions.length === 0 && riskAssessment.overallRisk === null) {
      setLoading(false);
      setError(new Error('No data available.'));
    } else {
      setLoading(false);
    }
  }, [nftPositions, riskAssessment]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
        <p className="text-gray-600">Loading data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md flex flex-col items-center">
        <h1 className="text-2xl font-bold mb-4 text-red-700">Error</h1>
        <p className="text-gray-600">Error: {error.message}</p>
      </div>
    );
  }

  const nftSummary = nftPositions.map((pos) => ({
    tokenId: pos.tokenId,
    quantity: pos.quantity,
    percentage: (pos.quantity / nftPositions.length) * 100,
  }));

  const chartData = {
    labels: nftSummary.map((item) => item.tokenId),
    datasets: [
      {
        label: 'NFT Quantity',
        data: nftSummary.map((item) => item.quantity),
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md flex flex-row">
      <div className="w-1/2 p-4">
        <h2 className="text-xl font-bold mb-4">NFT Portfolio Summary</h2>
        <canvas
          id="nftChart"
          width="400"
          height="200"
          className="mt-4"
        >
          <Chart data={chartData} type="bar" />
        </canvas>
      </div>
      <div className="w-1/2 p-4">
        <h2 className="text-xl font-bold mb-4">Risk Assessment</h2>
        <p className="text-gray-700">Overall Risk: {riskAssessment.overallRisk}</p>
        <p className="text-gray-700">High Risk: {riskAssessment.riskCategories.high}</p>
        <p className="text-gray-700">Medium Risk: {riskAssessment.riskCategories.medium}</p>
        <p className="text-gray-700">Low Risk: {riskAssessment.riskCategories.low}</p>
      </div>
    </div>
  );
};

export default Dashboard;