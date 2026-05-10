import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoinGecko } from './api/CoinGecko';
import { WebSocketClient } from './api/WebSocketClient';
import { RiskScoreData } from './types/RiskScoreData';
import { NFTHolderData } from './types/NFTHolderData';

const Tailwind = useTailwind();

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [riskScores, setRiskScores] = useState<Record<string, RiskScoreData> | {}>();
  const [nftHolders, setNftHolders] = useState<NFTHolderData[] | []>();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const gecko = new CoinGecko();
        const ws = new WebSocketClient();

        const cryptoPrices = await gecko.getPrices('ethereum', 'usd');
        const holderData = await ws.getNftHolders();
        const riskScoresData = await ws.getRiskScores(holderData.map(holder => holder.walletAddress));

        setRiskScores(riskScoresData);
        setNftHolders(holderData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  if (loading) {
    return (
      <div className={Tailwind('flex items-center justify-center h-screen')}>
        <p className={Tailwind('text-xl font-bold')}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={`${Tailwind('bg-gray-100 p-4')} ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
      <header className={Tailwind('bg-white shadow-md p-4 flex items-center justify-between')}>
        <h1 className={Tailwind('text-2xl font-bold')}>Mossland Vault Optimization</h1>
        <button className={Tailwind('bg-blue-500 text-white px-4 py-2 rounded')} onClick={toggleDarkMode}>
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </header>

      <div className={Tailwind('flex')}>
        <aside className={Tailwind('w-64 bg-gray-200 p-4')}>
          {/* Sidebar content */}
          <h2 className={Tailwind('text-lg font-bold mb-2')}>NFT Holder Dashboard</h2>
          <button className={Tailwind('bg-gray-300 hover:bg-gray-400 px-4 py-2 rounded')} onClick={() => {}}>
            Refresh Holders
          </button>
        </aside>

        <main className={Tailwind('w-full flex-grow p-4')}>
          {/* Main Content */}
          <div className={Tailwind('grid grid-cols-1 sm:grid-cols-2 gap-4')}>
            {/* Risk Score Dashboard */}
            <div className={Tailwind('bg-white rounded shadow-md p-4 w-full'}>
              <h3 className={Tailwind('text-lg font-bold mb-2')}>Risk Score Dashboard</h3>
              {Object.keys(riskScores).map((walletAddress) => (
                <RiskScoreDashboard key={walletAddress} walletAddress={walletAddress} data={riskScores[walletAddress]} />
              ))}
            </div>

            {/* NFT Holder Details */}
            <div className={Tailwind('bg-white rounded shadow-md p-4 w-full')}>
              <h3 className={Tailwind('text-lg font-bold mb-2')}>NFT Holder Details</h3>
              {nftHolders.map((holder) => (
                <NFTHolderDetails key={holder.walletAddress} data={holder} />
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

interface RiskScoreDashboardProps {
  walletAddress: string;
  data: RiskScoreData;
}

const RiskScoreDashboard = ({ walletAddress, data }: RiskScoreDashboardProps) => {
  return (
    <div className={Tailwind('border rounded p-4')}>
      <p className={Tailwind('text-lg font-bold mb-2')}>Wallet Address: {walletAddress}</p>
      <p className={Tailwind('text-gray-700 mb-2')}>Risk Score: {data.riskScore}</p>
      <p className={Tailwind('text-gray-700 mb-2')}>Confidence Level: {data.confidenceLevel}</p>
      {/* Add more risk score details here */}
    </div>
  );
};

interface NFTHolderDetailsProps {
  data: NFTHolderData;
}

const NFTHolderDetails = ({ data }: NFTHolderDetailsProps) => {
  return (
    <div className={Tailwind('border rounded p-4')}>
      <p className={Tailwind('text-lg font-bold mb-2')}>Wallet Address: {data.walletAddress}</p>
      <p className={Tailwind('text-gray-700 mb-2')}>NFT Holdings:</p>
      {/* Display NFT holdings here */}
    </div>
  );
};

export default Dashboard;