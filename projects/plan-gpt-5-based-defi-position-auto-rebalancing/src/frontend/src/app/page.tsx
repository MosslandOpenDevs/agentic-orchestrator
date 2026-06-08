import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoingeckoAPI, DefiLlamaAPI } from './api';
import { WebSocketClient } from 'websocket';

// Mock data for demonstration purposes
interface NFT {
  tokenId: string;
  name: string;
  nftType: string;
  quantity: number;
}

interface Position {
  nft: NFT;
  amount: number;
}

interface RiskAssessmentData {
  riskLevel: string;
  potentialLoss: number;
}

type WebSocketMessage = {
  type: 'positionUpdate';
  data: Position;
};

type AppState = {
  nftPositions: Position[];
  cryptoPrices: { [symbol: string]: number };
  defiLlamaData: { tvl: number };
  riskAssessment: RiskAssessmentData | null;
  loading: boolean;
  darkMode: boolean;
};

const App: React.FC = () => {
  const tailwind = useTailwind();
  const [state, setState] = useState<AppState>({
    nftPositions: [],
    cryptoPrices: {},
    defiLlamaData: { tvl: 0 },
    riskAssessment: null,
    loading: true,
    darkMode: false,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Mock NFT positions
        const mockNFTs: NFT[] = [
          { tokenId: 'Mossland1', name: 'Mossland NFT 1', nftType: 'Land', quantity: 10 },
          { tokenId: 'Mossland2', name: 'Mossland NFT 2', nftType: 'Land', quantity: 5 },
        ];
        const mockPositions: Position[] = mockNFTs.map(nft => ({ nft, amount: Math.floor(Math.random() * 100) }));

        // Fetch crypto prices
        const cryptoPrices = await CoingeckoAPI.getPrices(['BTC', 'ETH', 'USDT']);

        // Fetch DeFi Llama TVL
        const defiLlamaData = await DefiLlamaAPI.getTVL();

        // Simulate risk assessment
        const riskAssessment = { riskLevel: 'Medium', potentialLoss: 50 };

        setState({
          nftPositions: mockPositions,
          cryptoPrices,
          defiLlamaData,
          riskAssessment,
          loading: false,
        });
      } catch (error) {
        console.error('Error fetching data:', error);
        setState({ loading: false });
      }
    };

    fetchData();
  }, []);

  // WebSocket setup (placeholder)
  const ws = new WebSocketClient({ port: 8080, rejectUnauthorized: false });

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'positionUpdate') {
      setState(prevState => {
        const newPositions = [...prevState.nftPositions, message.data];
        return { ...prevState, nftPositions: newPositions };
      });
    }
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
  };

  ws.onopen = () => {
    console.log('WebSocket opened');
  };

  if (state.loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-xl font-bold')}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={tailwind('flex h-screen')}>
      {/* Sidebar */}
      <aside className={tailwind('bg-gray-200 p-4')}>
        <h2 className={tailwind('text-lg font-bold mb-2')}>NFT Portfolio</h2>
        {/* Add navigation links here */}
      </aside>

      {/* Main Content */}
      <main className={tailwind('flex-grow p-4')}>
        {/* Header */}
        <header className={tailwind('bg-white shadow-md p-4')}>
          <h1 className={tailwind('text-3xl font-bold mb-2')}>Mossland DeFi Agent</h1>
          <button className={tailwind('bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded')} onClick={() => setState({...state, darkMode: !state.darkMode})}>
            {state.darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
        </header>

        {/* Dashboard Content */}
        <div className={tailwind('p-4')}>
          {/* NFT Portfolio Overview */}
          <div className={tailwind('mb-4')}>
            <h2 className={tailwind('text-2xl font-bold mb-2')}>NFT Positions</h2>
            {state.nftPositions.map(position => (
              <div key={position.nft.tokenId} className={tailwind('border rounded-md p-4 mb-2')}>
                <p className={tailwind('text-lg font-semibold')}>
                  {position.nft.name} ({position.nft.nftType}) - {position.amount}
                </p>
              </div>
            ))}
          </div>

          {/* Crypto Prices */}
          <div className={tailwind('mb-4')}>
            <h2 className={tailwind('text-2xl font-bold mb-2')}>Crypto Prices</h2>
            <div className={tailwind('grid grid-cols-3 gap-4')}>
              {Object.entries(state.cryptoPrices).map(([symbol, price]) => (
                <div key={symbol} className={tailwind('bg-white rounded-md p-4')}>
                  <p className={tailwind('text-xl font-semibold')}>{symbol}</p>
                  <p className={tailwind('text-lg font-normal')}>${price.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* DeFi Llama TVL */}
          <div className={tailwind('mb-4')}>
            <h2 className={tailwind('text-2xl font-bold mb-2')}>DeFi Llama TVL</h2>
            <p className={tailwind('text-lg font-normal')}>${state.defiLlamaData.tvl.toFixed(2)}</p>
          </div>

          {/* Risk Assessment */}
          <div className={tailwind('mb-4')}>
            <h2 className={tailwind('text-2xl font-bold mb-2')}>Risk Assessment</h2>
            {state.riskAssessment ? (
              <p className={tailwind('text-lg font-normal')}>
                Risk Level: {state.riskAssessment.riskLevel}, Potential Loss: ${state.riskAssessment.potentialLoss.toFixed(2)}
              </p>
            ) : (
              <p className={tailwind('text-lg font-normal')}>Risk assessment not available.</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;