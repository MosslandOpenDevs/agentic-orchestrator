import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoinGecko } from './api/CoinGecko';
import { OpenAI } from './api/OpenAI';
import { WebSocketClient } from 'websocket';

// Component imports
import NFTCard from './components/NFTCard';
import PortfolioOverview from './components/PortfolioOverview';
import RiskAlerts from './components/RiskAlerts';
import { useColorScheme } from 'next/types';

const Dashboard = () => {
  const [nftData, setNftData] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any>({
    assets: [],
    totalValue: 0,
    riskScore: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [riskAlerts, setRiskAlerts] = useState<string[]>([]);
  const tailwind = useTailwind();
  const colorScheme = useColorScheme();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // NFT Data Retrieval
        const nftResponse = await CoinGecko.getNFTData();
        setNftData(nftResponse);
        setError(null);
      } catch (err) {
        setError('Failed to fetch NFT data.');
        console.error('Error fetching NFT data:', err);
      }

      // Portfolio Data Retrieval
      try {
        const portfolioData = await CoinGecko.getPortfolioData();
        setPortfolio(portfolioData);
        setError(null);
      } catch (err) {
        setError('Failed to fetch portfolio data.');
        console.error('Error fetching portfolio data:', err);
      }

      setLoading(false);
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (portfolio.assets.length > 0) {
      // Risk Calculation (Simplified - Replace with actual logic)
      const riskScore = portfolio.assets.reduce((acc, asset) => acc + asset.value * 0.1, 0);
      setPortfolio((prevPortfolio) => ({
        ...prevPortfolio,
        riskScore: riskScore,
      }));
    }
  }, [portfolio]);

  useEffect(() => {
    // Placeholder for Risk Alerts - Replace with actual alert logic
    if (portfolio.riskScore > 70) {
      setRiskAlerts(['High risk detected! Review your portfolio carefully.']);
    } else {
      setRiskAlerts([]);
    }
  }, [portfolio.riskScore]);

  if (loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-xl text-gray-500')}>
          Loading data...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-red-500 text-xl')}>
          Error: {error}
        </p>
      </div>
    );
  }

  return (
    <div className={tailwind('min-h-screen bg-gray-100')}>
      <header className={tailwind('bg-white shadow-md p-4')}>
        <h1 className={tailwind('text-2xl font-bold text-gray-800')}>
          TerraNova - NFT Valuation & Portfolio Optimization
        </h1 className={tailwind('text-2xl font-bold text-gray-800')}>
        </header>
      <main className={tailwind('p-4')}>
        <PortfolioOverview portfolio={portfolio} />
        <section className={tailwind('grid grid-cols-1 md:grid-cols-3 gap-4')}>
          {nftData.map((nft) => (
            <NFTCard key={nft.id} nft={nft} />
          ))}
        </section>
        <RiskAlerts alerts={riskAlerts} />
      </main>
    </div>
  );
};

export default Dashboard;