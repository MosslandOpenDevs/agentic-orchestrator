import React, { useState, useEffect } from 'react';
import { useServerApi } from '../../utils/serverApi'; // Assuming serverApi is defined elsewhere
import { Chart } from 'chart.js';

interface PortfolioItem {
  asset: string;
  balance: number;
  performance: number;
  // Add other asset properties as needed
}

interface PortfolioDashboardProps {
  userId: string;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioItem[] | null>(null);

  const { getPortfolioData } = useServerApi();

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const data = await getPortfolioData(userId);
        setPortfolioData(data);
        setLoading(false);
      } catch (err: any) {
        setError(err);
        setLoading(false);
      }
    };

    fetchPortfolio();
  }, [userId, getPortfolioData]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md">
        <p>Error loading portfolio data: {error.message}</p>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md flex items-center justify-center">
        <p>No portfolio data available.</p>
      </div>
    );
  }

  // Example Chart Data - Replace with actual chart data
  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Performance',
        data: portfolioData.map(item => item.performance),
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: {
          display: true,
          text: 'Month'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Performance (%)'
        }
      }
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md flex">
      <div className="w-3/4">
        <h2 className="text-xl font-bold mb-4">Portfolio Overview</h2>
        <table className="w-full table-auto">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 text-left">Asset</th>
              <th className="px-4 py-2 text-left">Balance</th>
              <th className="px-4 py-2 text-left">Performance</th>
            </tr>
          </thead>
          <tbody>
            {portfolioData.map(item => (
              <tr key={item.asset} className="hover:bg-gray-200">
                <td className="px-4 py-2">{item.asset}</td>
                <td className="px-4 py-2">{item.balance.toFixed(2)}</td>
                <td className="px-4 py-2">{item.performance.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-4">
          <h3 className="text-xl font-bold mb-2">Performance Visualization</h3>
          <canvas id="performanceChart" className="w-full h-48" {...chartOptions}></canvas>
        </div>
      </div>

      <div className="w-1/4">
        <h3 className="text-xl font-bold mb-2">Rebalancing Controls</h3>
        {/* Placeholder for rebalancing controls - Implement actual controls here */}
        <p>Rebalancing controls would go here.</p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;