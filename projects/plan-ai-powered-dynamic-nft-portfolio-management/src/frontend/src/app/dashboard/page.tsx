import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeftOut } from '@heroicons/react/24/solid';
import {
  ChartBar,
  DollarSign,
  ShieldExclamation,
  ArrowDownCircle,
  ArrowUpCircle,
} from '@heroicons/react/24/outline';

interface PortfolioData {
  totalValue: number;
  assets: {
    stocks: {
      name: string;
      quantity: number;
      price: number;
    }[];
    bonds: {
      name: string;
      quantity: number;
      price: number;
    }[];
    cash: {
      amount: number;
    };
  };
}

interface RiskProfile {
  name: string;
  description: string;
  riskLevel: 'low' | 'medium' | 'high';
}

interface OptimizationRecommendation {
  title: string;
  description: string;
  action: string;
}

const Dashboard = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data
    const fetchData = async () => {
      try {
        const data: PortfolioData = {
          totalValue: 123456.78,
          assets: {
            stocks: [
              { name: 'Apple', quantity: 10, price: 150 },
              { name: 'Google', quantity: 5, price: 2500 },
            ],
            bonds: [{ name: 'US Treasury', quantity: 2, price: 105 }],
            cash: { amount: 1000 },
          },
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

  const riskProfiles: RiskProfile[] = [
    { name: 'Conservative', description: 'Low risk, steady growth.', riskLevel: 'low' },
    { name: 'Moderate', description: 'Balanced risk and reward.', riskLevel: 'medium' },
    { name: 'Aggressive', description: 'High risk, potential for high growth.', riskLevel: 'high' },
  ];

  const optimizationRecommendations: OptimizationRecommendation[] = [
    { title: 'Diversify Portfolio', description: 'Consider adding more asset classes to reduce risk.', action: 'Review Asset Allocation' },
    { title: 'Rebalance Portfolio', description: 'Bring your portfolio back to your target risk level.', action: 'Execute Rebalancing' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-xl">Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500 text-xl">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <button
            onClick={() => router.go(-1)}
            aria-label="Go Back"
            className="bg-gray-300 hover:bg-gray-400 text-gray-800 text-lg font-bold py-2 px-4 rounded-md"
          >
            <ArrowLeftOut />
          </button>
        </div>
        <div className="ml-4">
          <h1 className="text-3xl font-bold text-gray-800">Portfolio Dashboard</h1>
        </div>
      </div>

      <div className="mt-4">
        <section className="mb-4">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Portfolio Overview</h2>
          <div className="flex items-center mb-4">
            <DollarSign className="text-3xl text-green-500 mr-2" />
            <p className="text-xl font-semibold text-gray-800">
              ${portfolioData?.totalValue.toFixed(2)}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {portfolioData?.assets.stocks.map((stock) => (
              <div key={stock.name} className="bg-white rounded-md shadow-md p-4">
                <h3 className="text-xl font-bold text-gray-800 mb-2">{stock.name}</h3>
                <p className="text-gray-600">Quantity: {stock.quantity}</p>
                <p className="text-gray-600">Price: ${stock.price.toFixed(2)}</p>
              </div>
            ))}
            {portfolioData?.assets.bonds.length > 0 && (
              <div key="bonds" className="bg-white rounded-md shadow-md p-4">
                <h3 className="text-xl font-bold text-gray-800 mb-2">Bonds</h3>
                {portfolioData?.assets.bonds.map((bond) => (
                  <div key={bond.name} className="bg-white rounded-md shadow-md p-4">
                    <p className="text-xl font-bold text-gray-800 mb-2">{bond.name}</p>
                    <p className="text-gray-600">Quantity: {bond.quantity}</p>
                    <p className="text-gray-600">Price: ${bond.price.toFixed(2)}</p>
                  </div>
                ))}
              </div>
            )}
            {portfolioData?.assets.cash.amount > 0 && (
              <div key="cash" className="bg-white rounded-md shadow-md p-4">
                <h3 className="text-xl font-bold text-gray-800 mb-2">Cash</h3>
                <p className="text-gray-600">Amount: ${portfolioData?.assets.cash.amount.toFixed(2)}</p>
              </div>
            )}
          </div>
        </section>

        <section className="mb-4">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Risk Profile</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {riskProfiles.map((profile) => (
              <button
                key={profile.name}
                className={`bg-gray-300 hover:bg-gray-400 text-gray-800 text-lg font-bold py-2 px-4 rounded-md ${
                  profile.riskLevel === 'low'
                    ? 'border-blue-500'
                    : profile.riskLevel === 'medium'
                      ? 'border-green-500'
                      : 'border-red-500'
                }`}
                aria-label={`Select ${profile.name} Risk Profile`}
                onClick={() => router.push(`/risk/${profile.riskLevel}`)}
              >
                {profile.name}
              </button>
            ))}
          </div>
        </section>

        <section className="mb-4">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Optimization Recommendations</h2>
          <div className="flex flex-col items-start">
            {optimizationRecommendations.map((recommendation) => (
              <div
                key={recommendation.title}
                className="bg-white rounded-md shadow-md p-4 mb-4"
              >
                <h3 className="text-xl font-bold text-gray-800 mb-2">{recommendation.title}</h3>
                <p className="text-gray-600">{recommendation.description}</p>
                <button
                  className={`bg-blue-500 hover:bg-blue-700 text-white text-lg font-bold py-2 px-4 rounded-md ${
                    recommendation.action === 'Review Asset Allocation'
                      ? 'uppercase'
                      : ''
                  }`}
                  onClick={() => {
                    if (recommendation.action === 'Review Asset Allocation') {
                      router.push('/asset-allocation');
                    }
                  }}
                  aria-label={recommendation.action}
                >
                  {recommendation.action}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;