import React, { useState, useEffect } from 'react';
import { FaArrowDown, FaArrowUp } from 'react-icons/fa';
import { Chart as ChartJS, Title, Label, LineElement, CategoryScale } from 'chart.js';
import { Line } from 'react-chartjs-2';
import CoinGecko from 'coin-gecko';
import { ethers } from 'ethers';
import { WebSocket } from 'ws';

// Mock data for demonstration
interface SecurityToken {
  id: string;
  name: string;
  price: number;
  symbol: string;
}

interface RebalancingRecommendation {
  securityId: string;
  action: 'buy' | 'sell';
  amount: number;
}

const App: React.FC = () => {
  const [securityTokens, setSecurityTokens] = useState<SecurityToken[]>([]);
  const [recoms, setRecoms] = useState<RebalancingRecommendation[]>([]);
  const [cryptoData, setCryptoData] = useState<any>({} as any);
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Mock security tokens
        const mockTokens: SecurityToken[] = [
          { id: 'BTC', name: 'Bitcoin', price: 35000, symbol: 'BTC' },
          { id: 'ETH', name: 'Ethereum', price: 2000, symbol: 'ETH' },
          { id: 'BNB', name: 'Binance Coin', price: 300, symbol: 'BNB' },
        ];
        setSecurityTokens(mockTokens);

        // Mock rebalancing recommendations
        const mockRecoms: RebalancingRecommendation[] = [
          { securityId: 'BTC', action: 'buy', amount: 0.1 },
          { securityId: 'ETH', action: 'sell', amount: 0.05 },
        ];
        setRecoms(mockRecoms);

        // Fetch crypto data
        const cg = new CoinGecko();
        await cg.coins.detail('bitcoin').then(res => setCryptoData(res.data));
        await cg.coins.detail('ethereum').then(res => setCryptoData(res));
        await cg.coins.detail('binancecoin').then(res => setCryptoData(res));

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleDarkModeToggle = () => {
    setDarkMode(!darkMode);
  };

  const chartData = {
    labels: Array.from({ length: 10 }, (_, i) => i),
    datasets: [
      {
        label: 'Price',
        data: [34000, 36000, 38000, 40000, 42000, 44000, 46000, 48000, 50000, 52000],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  return (
    <div className={`app ${darkMode ? 'dark-mode' : ''}`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <span onClick={handleDarkModeToggle} className="text-blue-500 cursor-pointer">
          🌙
        </span>
        <h1>DeepSynapse</h1>
      </header>

      <main className="container mx-auto p-4">
        {loading ? (
          <div className="text-center mt-8">Loading data...</div>
        ) : (
          <div>
            <section className="mb-8">
              <h2>Security Portfolio</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {securityTokens.map((token) => (
                  <div key={token.id} className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg">
                    <h3 className="text-lg font-semibold">{token.name}</h3>
                    <p className="text-gray-600">Symbol: {token.symbol}</p>
                    <p className="text-xl font-bold">Price: ${token.price}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="mb-8">
              <h2>Rebalancing Recommendations</h2>
              <div className="table-container">
                <table className="table-auto">
                  <thead>
                    <tr>
                      <th>Security</th>
                      <th>Action</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recoms.map((recom) => (
                      <tr key={recom.securityId}>
                        <td>{recom.securityId}</td>
                        <td>
                          {recom.action === 'buy' ? (
                            <FaArrowUp className="text-green-500" />
                          ) : (
                            <FaArrowDown className="text-red-500" />
                          )}
                        </td>
                        <td>{recom.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="mb-8">
              <h2>Price Chart</h2>
              <Line data={chartData} options={{
                scales: {
                  y: {
                    beginAtZero: true
                  }
                }
              }}/>
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;