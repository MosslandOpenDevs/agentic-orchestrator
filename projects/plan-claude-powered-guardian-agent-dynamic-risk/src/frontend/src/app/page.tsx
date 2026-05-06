import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart as ChartJS, Title } from 'chart.js';
import { Line } from 'chart.js';

// Placeholder data - Replace with actual data fetching
interface PortfolioData {
  assets: {
    name: string;
    quantity: number;
    price: number;
  }[];
}

// Placeholder data - Replace with actual data fetching
interface RiskProfile {
  riskTolerance: number;
  investmentHorizon: string;
}

type PortfolioState = {
  portfolioData: PortfolioData | null;
  riskProfile: RiskProfile | null;
  loading: boolean;
  error: string | null;
};

const Dashboard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const portfolioId = searchParams.get('portfolioId') || 'defaultPortfolio';
  const [portfolioState, setPortfolioState] = useState<PortfolioState>({
    portfolioData: null,
    riskProfile: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    // Simulate fetching data
    const fetchData = async () => {
      try {
        // Simulate fetching portfolio data
        const portfolioData = {
          assets: [
            { name: 'Mossland NFT', quantity: 10, price: 100 },
            { name: 'ETH', quantity: 50, price: 3000 },
          ],
        };

        // Simulate fetching risk profile
        const riskProfile = {
          riskTolerance: 7,
          investmentHorizon: 'Long Term',
        };

        setPortfolioState({
          portfolioData,
          riskProfile,
          loading: false,
          error: null,
        });
      } catch (error) {
        setPortfolioState({
          portfolioData: null,
          riskProfile: null,
          loading: false,
          error: 'Failed to fetch data',
        });
      }
    };

    fetchData();
  }, []);

  if (portfolioState.loading) {
    return <div>Loading...</div>;
  }

  if (portfolioState.error) {
    return <div>Error: {portfolioState.error}</div>;
  }

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>Guardian Dashboard</h1>
        <nav>
          <ul className="flex space-x-4">
            <li>Portfolio</li>
            <li>Risk Profile</li>
          </ul>
        </nav>
      </header>

      <main className="mt-8 flex">
        <aside className="w-64 bg-gray-700 p-4">
          <h2>Risk Profile</h2>
          <p>Risk Tolerance: {portfolioState.riskProfile?.riskTolerance}</p>
          <p>Investment Horizon: {portfolioState.riskProfile?.investmentHorizon}</p>
        </aside>

        <section className="flex-grow ml-4">
          <h2>Portfolio Details</h2>
          <p>Portfolio ID: {portfolioId}</p>
          <h3>Assets</h3>
          {portfolioState.portfolioData?.assets.map((asset) => (
            <div key={asset.name} className="mb-2">
              <p>{asset.name}: {asset.quantity} units at ${asset.price}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;