import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';

// Placeholder data - replace with actual data from WebSocket
interface PortfolioItem {
  tokenId: string;
  quantity: number;
  price: number;
}

interface AgentReceipt {
  id: string;
  agentId: string;
  startTime: string;
  endTime: string;
  status: 'active' | 'completed' | 'failed';
  results: PortfolioItem[];
}

type PortfolioData = {
  portfolio: PortfolioItem[];
  agentReceipts: AgentReceipt[];
};

const Dashboard: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData>({
    portfolio: [],
    agentReceipts: [],
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const simulateData = () => {
      const portfolio: PortfolioItem[] = [
        { tokenId: 'NFT1', quantity: 10, price: 100 },
        { tokenId: 'NFT2', quantity: 5, price: 200 },
      ];
      const agentReceipts: AgentReceipt[] = [
        { id: 'AR1', agentId: 'AG1', startTime: '2024-01-01T10:00:00Z', endTime: '2024-01-01T12:00:00Z', status: 'completed', results: portfolio },
        { id: 'AR2', agentId: 'AG2', startTime: '2024-01-02T10:00:00Z', endTime: '2024-01-02T12:00:00Z', status: 'active', results: portfolio },
      ];
      setPortfolioData({ portfolio, agentReceipts });
    };

    // Simulate WebSocket data - replace with actual WebSocket connection
    const intervalId = setInterval(() => {
      simulateData();
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  const toggleTheme = () => {
    setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  return (
    <div className={`min-h-screen ${theme === 'light' ? 'bg-gray-100' : 'bg-gray-800'} transition-colors duration-300`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <button onClick={toggleTheme} className="text-gray-500">
          {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
        </button>
        <h1 className="text-xl font-bold">VALO Dashboard</h1>
      </header>

      <div className="flex">
        <aside className="bg-gray-800 p-4 w-64">
          {/* Sidebar content */}
          <h2 className="text-lg font-bold mb-2">Navigation</h2>
          <ul>
            <li><a href="#" className="block p-2 text-gray-300 hover:bg-gray-700">Portfolio</a></li>
            <li><a href="#" className="block p-2 text-gray-300 hover:bg-gray-700">Agent Receipts</a></li>
            <li><a href="#" className="block p-2 text-gray-300 hover:bg-gray-700">Risk Analysis</a></li>
          </ul>
        </aside>

        <main className="p-4 flex-grow">
          {/* Main Content */}
          <section className="md:w-3/4">
            <h2 className="text-lg font-bold mb-4">Portfolio Overview</h2>
            <PortfolioDashboard portfolioData={portfolioData.portfolio} />
          </section>

          <section className="md:w-3/4">
            <h2 className="text-lg font-bold mb-4">Agent Receipt Details</h2>
            <AgentReceiptDetails agentReceipts={portfolioData.agentReceipts} />
          </section>

          <section className="md:w-3/4">
            <h2 className="text-lg font-bold mb-4">Risk Analysis</h2>
            <RiskAnalysisChart portfolioData={portfolioData.portfolio} />
          </section>
        </main>
      </div>
    </div>
  );
};

const PortfolioDashboard = ({ portfolio }: { portfolio: PortfolioItem[] }) => (
  <div>
    <h3 className="text-lg font-bold mb-2">Portfolio</h3>
    {portfolio.map(item => (
      <div key={item.tokenId} className="mb-2">
        <p>Token ID: {item.tokenId}</p>
        <p>Quantity: {item.quantity}</p>
        <p>Price: {item.price}</p>
      </div>
    ))}
  </div>
);

const AgentReceiptDetails = ({ agentReceipts }: { agentReceipts: AgentReceipt[] }) => (
  <div>
    <h3 className="text-lg font-bold mb-2">Agent Receipt Details</h3>
    {agentReceipts.map(receipt => (
      <div key={receipt.id} className="mb-2">
        <p>ID: {receipt.id}</p>
        <p>Agent ID: {receipt.agentId}</p>
        <p>Status: {receipt.status}</p>
      </div>
    ))}
  </div>
);

const RiskAnalysisChart = ({ portfolio }: { portfolio: PortfolioItem[] }) => (
  <div>
    <h3 className="text-lg font-bold mb-2">Risk Analysis</h3>
    {/* Placeholder for chart - replace with Chart.js implementation */}
    <canvas id="riskChart" width="400" height="200"></canvas>
  </div>
);

export default Dashboard;