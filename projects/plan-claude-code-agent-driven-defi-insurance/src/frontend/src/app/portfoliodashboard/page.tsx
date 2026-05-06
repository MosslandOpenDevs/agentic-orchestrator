import React, { useState, useEffect } from 'react';
import { useServer } from '../../hooks/useServer'; // Assuming useServer hook is in this location
import { Chart } from 'chart.js';

interface PortfolioData {
  assets: {
    [asset: string]: {
      balance: number;
      price: number;
    };
  };
  yieldPerformance: {
    [asset: string]: {
      dailyYield: number;
      weeklyYield: number;
    };
  };
  riskAssessment: {
    overallRisk: number;
    riskCategories: {
      [category: string]: number;
    };
  };
}

interface PortfolioDashboardProps {
  userId: string;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ userId }) => {
  const { portfolioData, loading, error } = useServer(userId);

  const [chartData, setChartData] = useState<Chart.IData>;

  useEffect(() => {
    if (portfolioData && portfolioData.assets && Object.keys(portfolioData.assets).length > 0) {
      const assetNames = Object.keys(portfolioData.assets);
      const data = assetNames.map(asset => ({
        label: asset,
        value: portfolioData.assets[asset].balance,
      }));

      setChartData({
        labels: assetNames,
        datasets: [{
          label: 'Asset Balance',
          data: data.map(d => d.value),
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      });
    } else {
      setChartData(null);
    }
  }, [portfolioData]);

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error loading portfolio data: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Portfolio Dashboard</h2>

      <div className="mb-4">
        <p className="text-gray-700">Overall Risk Assessment: {portfolioData.riskAssessment.overallRisk.toFixed(2)}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {Object.entries(portfolioData.assets).map(([assetName, assetData]) => (
          <div key={assetName} className="bg-gray-100 p-4 rounded-md shadow-sm">
            <h3 className="text-lg font-medium mb-2">{assetName}</h3>
            <p className="text-gray-700 mb-2">Balance: ${assetData.balance.toFixed(2)}</p>
            <p className="text-gray-700 mb-2">Price: ${assetData.price.toFixed(2)}</p>
            <p className="text-gray-700 mb-2">Daily Yield: {assetData.yieldPerformance[assetName]?.dailyYield ? assetData.yieldPerformance[assetName].dailyYield.toFixed(2) : 'N/A'}%</p>
            <p className="text-gray-700 mb-2">Weekly Yield: {assetData.yieldPerformance[assetName]?.weeklyYield ? assetData.yieldPerformance[assetName].weeklyYield.toFixed(2) : 'N/A'}%</p>
          </div>
        ))}
      </div>

      <div className="mt-6 mb-4">
        <p className="text-lg font-semibold mb-2">Asset Balance Chart</p>
        {chartData ? (
          <canvas
            id="assetBalanceChart"
            width="400"
            height="200"
          >
            <Chart
              type="bar"
              data={chartData}
              options={{
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Balance'
                    }
                  }
                },
                plugins: {
                  title: {
                    display: true,
                    text: 'Asset Balance'
                  }
                }
              }}
            />
          </canvas>
        ) : (
          <p>No chart data available.</p>
        )}
      </div>
    </div>
  );
};

export default PortfolioDashboard;