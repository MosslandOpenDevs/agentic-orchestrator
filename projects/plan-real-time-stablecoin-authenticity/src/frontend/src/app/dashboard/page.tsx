import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart } from 'chart.js';

// Define interfaces for data and props
interface StablecoinData {
  symbol: string;
  riskScore: number;
  transactionHistory: TransactionHistory[];
}

interface TransactionHistory {
  timestamp: string;
  amount: number;
  type: 'buy' | 'sell';
}

interface DashboardProps {
  initialStablecoins?: StablecoinData[];
}

const Dashboard: React.FC<DashboardProps> = ({ initialStablecoins = [] }) => {
  const [stablecoins, setStablecoins] = useState<StablecoinData[]>(initialStablecoins);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [transactionHistory, setTransactionHistory] = useState<TransactionHistory[]>([]);

  const { search } = useSearchParams();
  const symbol = search.get('symbol');

  useEffect(() => {
    if (symbol) {
      setSelectedSymbol(symbol);
      fetchData(symbol);
    } else {
      setSelectedSymbol(null);
    }
  }, [symbol]);

  const fetchData = async (symbol: string) => {
    setLoading(true);
    try {
      const response = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${symbol}&vs_currencies=usd`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      const riskScore = Math.random() * 100; // Simulate risk score
      const transactionHistoryData = await fetchTransactions(symbol);
      setStablecoins({ symbol: symbol, riskScore: riskScore, transactionHistory: transactionHistoryData });
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async (symbol: string) => {
    const transactions = [
      { timestamp: '2024-01-01T10:00:00Z', amount: 100, type: 'buy' },
      { timestamp: '2024-01-02T12:30:00Z', amount: 50, type: 'sell' },
      { timestamp: '2024-01-03T15:45:00Z', amount: 25, type: 'buy' },
    ];
    return transactions;
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!stablecoins) {
    return <div>No data available.</div>;
  }

  const chartData = {
    labels: ['Risk Score'],
    datasets: [{
      label: 'Risk Score',
      data: [stablecoins.riskScore],
      backgroundColor: 'rgba(255, 0, 0, 0.5)',
      borderColor: 'red',
      borderWidth: 1
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Stablecoin:</label>
        <input
          type="text"
          value={selectedSymbol || stablecoins.symbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="bg-gray-100 border rounded-md p-2 w-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Select Stablecoin"
        />
      </div>

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Risk Score: {stablecoins.riskScore.toFixed(2)}</p>
      </div>

      <Chart
        data={chartData}
        options={chartOptions}
        className="mt-4"
      />

      <div className="mb-4">
        <p className="text-gray-700 font-semibold">Transaction History:</p>
        <ul className="list-disc list-inside text-sm">
          {transactionHistory.map((item) => (
            <li
              key={item.timestamp}
              className="mb-1"
              aria-label={`Transaction: ${item.timestamp}`}
            >
              {item.timestamp} - {item.amount} USD - {item.type}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;