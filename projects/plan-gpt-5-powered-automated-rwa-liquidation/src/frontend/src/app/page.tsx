import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoingeckoAPI, OpenAIAPI } from './api'; // Assuming API modules
import WebSocketClient from './websocket'; // Assuming WebSocket Client

const Dashboard = () => {
  const { tailwind } = useTailwind();
  const [loading, setLoading] = useState(true);
  const [portfolioData, setPortfolioData] = useState<any>({
    assets: [],
    riskTolerance: 'Medium',
  });
  const [gptRecommendations, setGptRecommendations] = useState<any>(null);
  const [ws, setWs] = useState<WebSocketClient | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Portfolio Data
        const portfolio = await CoingeckoAPI.getPortfolioData();
        setPortfolioData(portfolio);

        // Fetch GPT Recommendations
        const gptResponse = await OpenAIAPI.getGPTRecommendations(portfolioData.riskTolerance);
        setGptRecommendations(gptResponse);

        // Connect to WebSocket
        setWs(new WebSocketClient());
        ws.connect();

        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-xl')}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={tailwind('min-h-screen bg-gray-100')}>
      <header className={tailwind('bg-white shadow-md p-4')}>
        <h1 className={tailwind('text-2xl font-bold text-gray-800')}>
          Mossland RWA Dashboard
        </h1>
      </header>

      <main className={tailwind('p-4')}>
        {/* Portfolio Dashboard */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>Portfolio Overview</h2>
          <p className={tailwind('text-gray-600')}>
            Risk Tolerance: {portfolioData.riskTolerance}
          </p>
          {/* Display Portfolio Assets (Placeholder) */}
          {portfolioData.assets.map((asset) => (
            <div key={asset.id} className={tailwind('p-2 rounded-md mb-2')}>
              <p>{asset.name}</p>
              <p>{asset.price}</p>
            </div>
          ))}
        </div>

        {/* RWA Details Component (Placeholder) */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>RWA Details</h2>
          {/* Display RWA Details (Placeholder) */}
        </div>

        {/* Simulation Results Component (Placeholder) */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>Simulation Results</h2>
          {/* Display Simulation Results (Placeholder) */}
        </div>

        {/* GPT-5 Recommendations */}
        {gptRecommendations && (
          <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
            <h2 className={tailwind('text-xl font-bold mb-2')}>GPT-5 Recommendations</h2>
            <p>{gptRecommendations.recommendation}</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;