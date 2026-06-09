import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { CoinGecko } from '../lib/coinGecko'; // Assuming CoinGecko integration
import { OpenAI } from '../lib/openai'; // Assuming OpenAI integration
import { WebSocketClient } from 'websocket';

// Placeholder components - Replace with actual implementations
const PortfolioDashboard = () => {
  return <div>Portfolio Dashboard</div>;
};

const RebalanceForm = () => {
  return <div>Rebalance Form</div>;
};

const RationaleDisplay = () => {
  return <div>Rationale Display</div>;
};

type PortfolioData = {
  assets: { [key: string]: number };
};

type RiskTolerance = {
  conservative: number;
  moderate: number;
  aggressive: number;
};

type RebalanceResult = {
  recommendations: string[];
};

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const userId = searchParams.get('userId') || '1'; // Default user ID
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance | null>(null);
  const [rebalanceResult, setRebalanceResult] = useState<RebalanceResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const data = await CoinGecko.getPortfolioData(userId);
        setPortfolioData(data);
      } catch (err) {
        setError('Failed to fetch portfolio data: ' + String(err));
      }
    };

    fetchPortfolio();
  }, [userId]);

  useEffect(() => {
    if (portfolioData) {
      setLoading(false);
    }
  }, [portfolioData]);

  const handleRiskToleranceChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setRiskTolerance({
      conservative: parseInt(value || '0', 10),
      moderate: parseInt(event.target.value || '0', 10),
      aggressive: parseInt(event.target.value || '0', 10),
    });
  };

  const handleRebalance = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await OpenAI.generateRebalancingRationale(
        portfolioData,
        riskTolerance
      );
      setRebalanceResult(response);
    } catch (err) {
      setError('Failed to generate rebalancing rationale: ' + String(err));
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 min-h-screen p-8">
      <header className="bg-white shadow-md">
        <h1 className="text-xl font-bold text-gray-800">Mossland Auto-Rebalance</h1>
      </header>

      <main className="mt-8">
        <section className="mb-4">
          <PortfolioDashboard />
          <RebalanceForm onChange={handleRiskToleranceChange} />
          <button
            onClick={handleRebalance}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Rebalance
          </button>
        </section>

        <section className="mb-4">
          <RationaleDisplay rebalanceResult={rebalanceResult} />
        </section>
      </main>
    </div>
  );
};

export default Dashboard;