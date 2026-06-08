import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart } from 'chart.js';

interface PortfolioData {
  name: string;
  assets: Asset[];
}

interface Asset {
  name: string;
  type: 'stock' | 'crypto' | 'bond';
  quantity: number;
  currentPrice: number;
}

interface RiskProfile {
  conservative: boolean;
  moderate: boolean;
  aggressive: boolean;
}

const UserDashboard = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [riskProfile, setRiskProfile] = useState<RiskProfile>({
    conservative: false,
    moderate: true,
    aggressive: false,
  });
  const router = useRouter();

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const response = await fetch('/api/portfolio'); // Replace with your API endpoint
        if (!response.ok) {
          throw new Error(`Failed to fetch portfolio data: ${response.status}`);
        }
        const data = await response.json();
        setPortfolioData(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  const handleRiskChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRiskProfile({
      ...riskProfile,
      [e.target.name]: e.target.checked,
    });
  };

  const generateChart = () => {
    if (!portfolioData || !portfolioData.assets || portfolioData.assets.length === 0) {
      return;
    }

    const ctx = document.getElementById('asset-performance-chart') as HTMLCanvasElement;
    if (!ctx) return;

    const data = {
      labels: portfolioData.assets.map((asset) => asset.name),
      datasets: [
        {
          label: 'Asset Value',
          data: portfolioData.assets.map((asset) => asset.quantity * asset.currentPrice),
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1,
        },
      ],
    };
    new Chart(ctx, {
      type: 'line',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  };

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">User Portfolio Dashboard</h1>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700">Risk Profile:</label>
        <div className="mt-1">
          <label className="mr-2">Conservative:</label>
          <input
            type="checkbox"
            name="conservative"
            checked={riskProfile.conservative}
            onChange={handleRiskChange}
            aria-label="Set conservative risk profile"
          />
        </div>
        <div className="mt-1">
          <label className="mr-2">Moderate:</label>
          <input
            type="checkbox"
            name="moderate"
            checked={riskProfile.moderate}
            onChange={handleRiskChange}
            aria-label="Set moderate risk profile"
          />
        </div>
        <div className="mt-1">
          <label className="mr-2">Aggressive:</label>
          <input
            type="checkbox"
            name="aggressive"
            checked={riskProfile.aggressive}
            onChange={handleRiskChange}
            aria-label="Set aggressive risk profile"
          />
        </div>
      </div>

      <div className="mb-4">
        {portfolioData && portfolioData.assets && (
          <>
            <h2 className="text-xl font-bold mb-2">Portfolio Overview</h2>
            {portfolioData.assets.map((asset) => (
              <div key={asset.name} className="mb-2">
                <p className="text-sm font-medium">{asset.name}</p>
                <p className="text-base">Type: {asset.type}</p>
                <p className="text-base">Quantity: {asset.quantity}</p>
                <p className="text-base">Current Price: ${asset.currentPrice}</p>
              </div>
            ))}
          </>
        )}
      </div>

      <canvas id="asset-performance-chart" width="400" height="200"></canvas>

      {/* Add more features and styling here */}
    </div>
  );
};

export default UserDashboard;