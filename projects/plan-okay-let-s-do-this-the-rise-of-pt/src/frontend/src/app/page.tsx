import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { CoinGeckoData } from '../types/CoinGeckoData';
import { EtherscanTransaction } from '../types/EtherscanTransaction';
import { WebSocket } from 'ws';

// Placeholder data - Replace with actual data fetching
const initialCoinGeckoData: CoinGeckoData[] = [
  { id: 'BTC', symbol: 'BTC', price: 10000 },
  { id: 'ETH', symbol: 'ETH', price: 2000 },
];

const initialEtherscanData: EtherscanTransaction[] = [];

type RiskProfile = 'low' | 'medium' | 'high';

type AppState = {
  vaultData: any; // Replace with actual vault data type
  assets: string[];
  riskProfile: RiskProfile;
  coinGeckoData: CoinGeckoData[];
  etherscanData: EtherscanTransaction[];
  loading: boolean;
  error: string | null;
};

const Dashboard: React.FC<AppState> = () => {
  const [searchParams] = useSearchParams();
  const riskProfileParam = searchParams.get('riskProfile') || 'medium';
  const [state, setState] = useState<AppState>({
    vaultData: null,
    assets: [],
    riskProfile: riskProfileParam as RiskProfile,
    coinGeckoData: initialCoinGeckoData,
    etherscanData: initialEtherscanData,
    loading: true,
    error: null,
  });

  useEffect(() => {
    // Simulate data fetching
    const fetchData = async () => {
      try {
        // Fetch CoinGecko data
        const geckoData: CoinGeckoData[] = await fetch('https://api.coingecko.com/api/v3/simple/prices?ids=bitcoin,ethereum&vs_currencies=usd').then(res => res.json());
        setState(prevState => ({
          ...prevState,
          coinGeckoData: geckoData,
          loading: false,
        }));
      } catch (error) {
        console.error('Error fetching CoinGecko data:', error);
        setState(prevState => ({
          ...prevState,
          error: 'Failed to fetch CoinGecko data',
          loading: false,
        }));
      }
    };

    fetchData();
  }, []);

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-white shadow-md p-4">
        {/* Navigation (Placeholder) */}
        <nav className="flex items-center space-x-4">
          <h1 className="text-xl font-bold">Mossland Dashboard</h1>
        </nav>
      </header>

      <main className="flex-grow">
        <aside className="bg-gray-200 p-4 w-64">
          {/* Sidebar (Placeholder) */}
          <h2 className="text-lg font-semibold mb-2">Risk Profile</h2>
          <select
            value={state.riskProfile}
            onChange={(e) =>
              setState(prevState => ({
                ...prevState,
                riskProfile: e.target.value as RiskProfile,
              }))
            }
            className="bg-white rounded-md p-2 mt-2"
          >
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
        </aside>

        <div className="ml-4">
          {/* Content Area */}
          {state.loading ? (
            <div className="text-center p-4">Loading data...</div>
          ) : state.error ? (
            <div className="text-red-500 p-4">Error: {state.error}</div>
          ) : (
            <>
              {/* Vault Dashboard (Placeholder) */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Vault Data</h3>
                {/* Placeholder for vault data display */}
                <p>Vault data will be displayed here.</p>
              </div>

              {/* Asset List (Placeholder) */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Assets</h3>
                <ul className="list-disc space-y-2">
                  {state.assets.map(asset => (
                    <li key={asset}>{asset}</li>
                  ))}
                </ul>
              </div>

              {/* Risk Profile Selector (Placeholder) */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Risk Profile</h3>
                <p>Selected Risk Profile: {state.riskProfile}</p>
              </div>

              {/* Data Visualization (Placeholder) */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">CoinGecko Data</h3>
                <p>BTC Price: {state.coinGeckoData[0].price}</p>
                <p>ETH Price: {state.coinGeckoData[1].price}</p>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;