import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface PortfolioHolding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  totalValue: number;
}

interface AgentReceipt {
  id: string;
  date: string;
  agent: string;
  amount: number;
  description: string;
}

interface PortfolioDashboardProps {
  holdings: PortfolioHolding[];
  agentReceipts: AgentReceipt[];
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ holdings, agentReceipts }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (holdings.length === 0 && agentReceipts.length === 0) {
      router.push('/404');
    }
  }, [holdings, agentReceipts, router]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>
        <p className="text-gray-500">Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Error</h1>
        <p className="text-red-500">Error loading data: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* Portfolio Holdings */}
      <div className="mb-4" aria-label="Portfolio Holdings">
        <h2 className="text-xl font-bold mb-2">Portfolio Holdings</h2>
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left">
              <th>Symbol</th>
              <th>Name</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Total Value</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((holding) => (
              <tr key={holding.symbol} className="text-left">
                <td>{holding.symbol}</td>
                <td>{holding.name}</td>
                <td>{holding.quantity}</td>
                <td>${holding.price.toFixed(2)}</td>
                <td>${holding.totalValue.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Agent Receipt Details */}
      <div className="mb-4" aria-label="Agent Receipts">
        <h2 className="text-xl font-bold mb-2">Agent Receipt Details</h2>
        <table className="table-auto w-full">
          <thead>
            <tr className="text-left">
              <th>Date</th>
              <th>Agent</th>
              <th>Amount</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {agentReceipts.map((receipt) => (
              <tr key={receipt.id} className="text-left">
                <td>{receipt.date}</td>
                <td>{receipt.agent}</td>
                <td>${receipt.amount.toFixed(2)}</td>
                <td>{receipt.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Visualized Risk Metrics (Placeholder - Replace with actual implementation) */}
      <div className="mb-4" aria-label="Risk Metrics">
        <h2 className="text-xl font-bold mb-2">Risk Metrics</h2>
        <p>Risk metrics visualization would go here. Placeholder content.</p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;