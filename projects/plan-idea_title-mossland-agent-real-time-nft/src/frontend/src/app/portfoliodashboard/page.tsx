import React, { useState, useEffect } from 'react';
import { useServer } from '../../hooks/useServer'; // Assuming useServer hook exists
import { Chart } from 'chart.js';

interface PortfolioData {
  assets: {
    [asset: string]: {
      name: string;
      quantity: number;
      price: number;
    };
  };
  riskScore: number;
  rebalancingRecommendations: string[];
}

interface PortfolioDashboardProps {
  initialPortfolioData?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialPortfolioData }) => {
  const { portfolioData, loading, error } = useServer();
  const [chartData, setChartData] = useState<ChartData | null>(null);

  useEffect(() => {
    if (portfolioData) {
      setChartData({
        labels: Object.keys(portfolioData.assets),
        datasets: [
          {
            label: 'Asset Value',
            data: Object.values(portfolioData.assets).map(asset => asset.quantity * asset.price),
            backgroundColor: 'rgba(54, 162, 235, 0.4)',
          },
        ],
      });
    }
  }, [portfolioData]);

  if (loading) {
    return <div>Loading Portfolio Data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Portfolio Summary</h2>
        <p className="text-gray-700">
          Total Portfolio Value: ${portfolioData.assets.length > 0 ? Object.values(portfolioData.assets).reduce((sum, asset) => sum + asset.quantity * asset.price, 0) : 0}
        </p>
        <p className="text-gray-700">
          Risk Score: {portfolioData.riskScore}
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Risk Assessment Visualization</h2>
        {chartData && (
          <canvas
            id="riskChart"
            width="400"
            height="200"
            className="rounded"
          >
            <Chart
              type="bar"
              data={chartData}
              options={{
                scales: {
                  y: {
                    beginAtZero: true,
                  },
                },
              }}
            />
          </canvas>
        )}
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Rebalancing Recommendations</h2>
        <ul className="list-disc text-gray-700 mb-4">
          {portfolioData.rebalancingRecommendations.map(recommendation => (
            <li key={recommendation} className="mb-1">
              {recommendation}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

interface ChartData {
  labels: string[];
  datasets: any[];
}

export default PortfolioDashboard;