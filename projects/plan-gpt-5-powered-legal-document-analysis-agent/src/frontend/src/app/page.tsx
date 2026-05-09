import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { NFTCard } from '../components/NFTCard';
import { PortfolioOverview } from '../components/PortfolioOverview';
import { RiskAlerts } from '../components/RiskAlerts';
import { CoingeckoData } from '../types/CoingeckoData';
import { OpenAIResponse } from '../types/OpenAIResponse';
import { WebSocket } from '../utils/WebSocket';

const Dashboard = () => {
  const [nftData, setNftData] = useState<CoingeckoData[]>([]);
  const [portfolioRisk, setPortfolioRisk] = useState<number>(0);
  const [optimizationRecommendations, setOptimizationRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  const [searchParams] = useSearchParams();
  const userId = searchParams.get('userId') || 'defaultUser';

  useEffect(() => {
    const fetchNftData = async () => {
      try {
        const data = await fetch(`${process.env.NEXT_PUBLIC_COINGEKO_API}/accounts/mossland-nft/${userId}`).then(res => res.json());
        setNftData(data);
      } catch (error) {
        console.error('Error fetching NFT data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchNftData();
  }, [userId]);

  useEffect(() => {
    if (nftData.length > 0) {
      calculatePortfolioRisk();
      generateOptimizationRecommendations();
    }
  }, [nftData]);

  const calculatePortfolioRisk = () => {
    // Placeholder - Replace with actual risk calculation logic
    const totalValuation = nftData.reduce((sum, item) => sum + item.price, 0);
    const volatility = 0.1; // Placeholder
    setPortfolioRisk(totalValuation * volatility);
  };

  const generateOptimizationRecommendations = () => {
    // Placeholder - Replace with actual recommendation engine logic
    setOptimizationRecommendations(['Consider diversifying your portfolio.', 'Monitor market volatility closely.']);
  };

  return (
    <div className={`min-h-screen dark-mode-${darkMode}`}>
      <header className="bg-gray-800 text-white py-4">
        <h1 className="text-2xl font-bold">Mossland NFT Portfolio</h1>
        <button onClick={() => setDarkMode(!darkMode)}>Toggle Dark Mode</button>
      </header>

      <main className="flex">
        <aside className="bg-gray-700 p-4 w-64">
          {/* Sidebar - Navigation, etc. */}
          <h2>Navigation</h2>
          <ul>
            <li>NFT Overview</li>
            <li>Portfolio Analysis</li>
            <li>Risk Alerts</li>
          </ul>
        </aside>

        <section className="p-4 flex">
          {loading ? (
            <div className="text-center">Loading NFT data...</div>
          ) : (
            <>
              <PortfolioOverview
                nftData={nftData}
                portfolioRisk={portfolioRisk}
                optimizationRecommendations={optimizationRecommendations}
              />
              <RiskAlerts
                portfolioRisk={portfolioRisk}
                optimizationRecommendations={optimizationRecommendations}
              />
            </>
          )}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;