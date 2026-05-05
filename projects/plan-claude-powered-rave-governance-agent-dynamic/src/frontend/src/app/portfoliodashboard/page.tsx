import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart } from 'chart.js';

interface PortfolioData {
  assets: {
    name: string;
    value: number;
    risk: number;
  }[];
}

interface PortfolioDashboardProps {
  initialData?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialData }) => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: PortfolioData = {
          assets: [
            { name: 'Stock A', value: 1000, risk: 0.5 },
            { name: 'Bond B', value: 500, risk: 0.2 },
            { name: 'Crypto C', value: 2000, risk: 0.8 },
          ],
        };
        setPortfolioData(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  const riskAssessment = portfolioData.assets
    .map((asset) => asset.risk)
    .reduce((sum, risk) => sum + risk, 0) / portfolioData.assets.length;

  const performanceChartData = {
    labels: portfolioData.assets.map((asset) => asset.name),
    datasets: [
      {
        label: 'Value',
        data: portfolioData.assets.map((asset) => asset.value),
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  // Chart.js setup
  useEffect(() => {
    const canvas = document.getElementById('performance-chart') as HTMLCanvasElement;
    if (canvas) {
      const chart = new Chart(canvas, {
        type: 'line',
        data: performanceChartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Asset Name',
              },
            },
            y: {
              title: {
                display: true,
                text: 'Value',
              },
            },
          },
        },
      });

      return () => {
        chart.destroy();
      };
    }
  }, [performanceChartData]);


  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Portfolio Summary</h2>
        <p className="text-gray-700">
          Total Portfolio Value: ${portfolioData.assets.reduce((sum, asset) => sum + asset.value, 0)}
        </p>
        <p className="text-gray-700">
          Average Risk: {riskAssessment.toFixed(2)}
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Risk Assessment</h2>
        <p className="text-gray-700">
          This section provides a risk assessment based on the portfolio's asset allocation.
        </p>
      </section>

      <section className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Performance Charts</h2>
        <canvas id="performance-chart" width="400" height="200"></canvas>
      </section>
    </div>
  );
};

export default PortfolioDashboard;