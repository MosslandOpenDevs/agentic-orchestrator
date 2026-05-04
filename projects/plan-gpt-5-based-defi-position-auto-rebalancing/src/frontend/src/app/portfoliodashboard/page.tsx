import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Chart as ChartJS, Title, Label, LineElement, LineCurve } from 'chart.js';
import { CategoryScale } from 'chart.js';

import {
  Bar,
  Line,
  Pie,
  Tooltip,
  Legend,
} from 'react-chartjs-2';

import {
  useWalletConnect,
} from '@walletconnect/react';

export default function PortfolioDashboard() {
  const [portfolioData, setPortfolioData] = useState<any>({} as any);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [rebalancingStrategy, setRebalancingStrategy] = useState<string>('conservative');
  const [transactionHistory, setTransactionHistory] = useState<any>({} as any);
  const router = useRouter();

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const response = await fetch('/api/portfolio', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ strategy: rebalancingStrategy }),
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch portfolio data: ${response.status}`);
        }

        const data = await response.json();
        setPortfolioData(data);
        setLoading(false);
        setError(null);
      } catch (error) {
        setError('Failed to load portfolio data. Please try again.');
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, [rebalancingStrategy]);

  useEffect(() => {
    const fetchTransactionHistory = async () => {
      try {
        const response = await fetch('/api/transactions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ strategy: rebalancingStrategy }),
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch transaction history: ${response.status}`);
        }

        const data = await response.json();
        setTransactionHistory(data);
      } catch (error) {
        setError('Failed to load transaction history. Please try again.');
      }
    };

    fetchTransactionHistory();
  }, [rebalancingStrategy]);


  const data = {
    labels: [],
    datasets: [
      {
        label: 'NFT Value',
        data: [],
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  if (loading) {
    return <div>Loading portfolio...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const chartOptions = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'NFT Portfolio Value',
      },
      legend: {
        display: true,
        position: 'top',
      },
    },
    scales: {
      x: {
        display: true,
      },
      y: {
        display: true,
      },
    },
    onClick: (event) => {
      // Handle click events on the chart
    },
    plugins: {
      tooltip: {
        enabled: true,
      },
    },
    plugins: {
      title: {
        display: true,
        text: 'NFT Portfolio Value',
      },
    },
    scales: {
      x: {
        display: true,
      },
      y: {
        display: true,
      },
    },
    plugins: {
      title: {
        display: true,
        text: 'NFT Portfolio Value',
      },
    },
    scales: {
      x: {
        display: true,
      },
      y: {
        display: true,
      },
    },
  };


  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">NFT Portfolio Dashboard</h1>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Rebalancing Strategy:</label>
        <select
          value={rebalancingStrategy}
          onChange={(e) => setRebalancingStrategy(e.target.value)}
          className="px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:ring-2 focus:ring-yellow-500"
          aria-label="Rebalancing Strategy"
        >
          <option value="conservative">Conservative</option>
          <option value="moderate">Moderate</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Portfolio Value:</p>
        <div className="text-4xl font-bold">{portfolioData?.totalValue || '0'}</div>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">
          <ChartJS
            url={{
              endpoint: '/api/chartData',
              method: 'POST',
              body: JSON.stringify({ strategy: rebalancingStrategy }),
            }}
            height={300}
            width={600}
          />
        </p>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Transaction History:</p>
        {transactionHistory && transactionHistory.length > 0 ? (
          <ul className="list-disc pl-5">
            {transactionHistory.map((transaction) => (
              <li key={transaction.id} className="text-gray-700">
                {transaction.type} - {transaction.amount}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-700">No transactions yet.</p>
        )}
      </div>
    </div>
  );
}