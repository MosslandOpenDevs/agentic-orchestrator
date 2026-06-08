import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJs,
  LineElement,
  CategoryScale,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { CoingeckoData } from '../types/coingecko';
import { RiskAssessmentData } from '../types/riskAssessment';
import { WebSocket } from 'ws';

// Mock data for demonstration purposes
interface AppState {
  portfolio: {
    btc: number;
    eth: number;
    usdt: number;
  };
  riskAssessment: RiskAssessmentData;
  loading: boolean;
  error: string | null;
}

const App: React.FC = () => {
  const [portfolio, setPortfolio] = useState<AppState['portfolio']>({
    btc: 10.0,
    eth: 5.0,
    usdt: 100.0,
  });
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentData>({
    riskScore: 0.6,
    description: 'Moderate Risk',
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate fetching data
        await new Promise(resolve => setTimeout(resolve, 2000));

        const coingeckoData: CoingeckoData = {
          BTC: 30000,
          ETH: 2000,
          USDT: 1,
        };

        setPortfolio({
          btc: coingeckoData.BTC,
          eth: coingeckoData.ETH,
          usdt: coingeckoData.USDT,
        });

        setRiskAssessment({
          riskScore: 0.6,
          description: 'Moderate Risk',
        });

        setLoading(false);
      } catch (err) {
        setError(String(err));
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div>
        Error: {error}
      </div>
    );
  }

  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'BTC Price',
        data: [30000, 32000, 35000, 33000, 31000],
        borderColor: 'rgb(75, 192, 192)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>Mossland GPT-5 Dashboard</h1>
        <div>
          <button className="bg-blue-500 text-white px-4 rounded">
            Dark Mode
          </button>
        </div>
      </header>

      <main className="p-4">
        {/* Portfolio Overview */}
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-2">Portfolio</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded p-4 shadow-md">
              <p>BTC: {portfolio.btc}</p>
              <p>ETH: {portfolio.eth}</p>
              <p>USDT: {portfolio.usdt}</p>
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-2">Risk Assessment</h2>
          <p>Risk Score: {riskAssessment.riskScore.toFixed(2)}</p>
          <p>{riskAssessment.description}</p>
        </div>

        {/* Data Visualization */}
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-2">BTC Price Chart</h2>
          <Line data={chartData} />
        </div>
      </main>
    </div>
  );
};

export default App;