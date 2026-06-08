import React, { useState, useEffect } from 'react';
import { useDarkMode } from './useDarkMode'; // Assuming you have this hook
import { CoinGeckoData } from './types'; // Assuming you have this type

// Placeholder data - Replace with actual API calls
const mockCoinGeckoData: CoinGeckoData[] = [
  { id: 'BTC', symbol: 'BTC', price: 65000 },
  { id: 'ETH', symbol: 'ETH', price: 3500 },
  { id: 'USDT', symbol: 'USDT', price: 1 },
];

function Dashboard() {
  const [darkMode, setDarkMode] = useDarkMode(false);

  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [riskProfile, setRiskProfile] = useState('moderate');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setPortfolioData({
        btc: 0.5,
        eth: 0.2,
        usdt: 1.0,
      });
      setLoading(false);
    }, 2000);
  }, []);

  const handleRiskProfileChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setRiskProfile(event.target.value);
  };

  return (
    <div className={`dashboard ${darkMode ? 'dark-mode' : ''}`}>
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>AI Portfolio Manager</h1>
        <button onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <main className="p-4 flex">
        <aside className="w-64 bg-gray-700 p-4">
          <h2>Risk Profile</h2>
          <select value={riskProfile} onChange={handleRiskProfileChange}>
            <option value="conservative">Conservative</option>
            <option value="moderate">Moderate</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </aside>

        <div className="w-full">
          {loading ? (
            <div className="text-center p-4">Loading portfolio data...</div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              <div className="bg-white p-4 rounded shadow-md">
                <h3>Portfolio Overview</h3>
                <p>
                  One-line Description: Automated DeFi portfolio optimization for Mossland NFT holders using AI, mitigating yield-seeking risk.
                </p>
                <p>
                  <b>Goals:</b> Optimize portfolio for long-term growth and risk mitigation.
                </p>
                <p>
                  <b>Target Users:</b> Mossland NFT Holders (estimated 1,000 - 5,000 initially, scaling with ecosystem growth).
                </p>
              </div>

              <div className="bg-white p-4 rounded shadow-md">
                <h3>Portfolio Details</h3>
                <p>BTC: {portfolioData?.btc || 'N/A'} USDT</p>
                <p>ETH: {portfolioData?.eth || 'N/A'} USDT</p>
                <p>USDT: {portfolioData?.usdt || 'N/A'} USDT</p>
              </div>

              {/* Placeholder for data visualization - Replace with actual charts */}
              <div className="bg-white p-4 rounded shadow-md">
                <h3>Performance Chart</h3>
                {/* Add chart component here */}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;