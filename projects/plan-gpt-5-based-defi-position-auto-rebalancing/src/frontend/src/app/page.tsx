import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoingeckoAPI } from './api/coingecko';
import { OpenAIAPI } from './api/openai';
import { WebSocketClient } from 'react-websockets';
import { useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area';
import { StatusBar } from 'react-native';

const App = () => {
  const tailwind = useTailwind();
  const [loading, setLoading] = useState(true);
  const [cryptoData, setCryptoData] = useState({});
  const [rebalanceRecommendations, setRebalanceRecommendations] = useState([]);
  const [openAIResponse, setOpenAIResponse] = useState('');
  const [ws, setWs] = useState(null);
  const [mode, setMode] = useState('light');

  useEffect(() => {
    const fetchCryptoData = async () => {
      try {
        const data = await CoingeckoAPI.getAssets();
        setCryptoData(data);
      } catch (error) {
        console.error('Error fetching crypto data:', error);
      }
    };

    fetchCryptoData();
  }, []);

  useEffect(() => {
    const fetchOpenAIResponse = async () => {
      try {
        const response = await OpenAIAPI.generateText('Analyze current DeFi market conditions and suggest potential rebalancing strategies.');
        setOpenAIResponse(response);
      } catch (error) {
        console.error('Error fetching OpenAI response:', error);
      }
    };

    fetchOpenAIResponse();
  }, []);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocketClient({
        uri: 'ws://localhost:8080', // Replace with your WebSocket server URI
      });

      ws.onOpen = () => {
        console.log('WebSocket connected');
      };

      ws.onMessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          setRebalanceRecommendations(data.recommendations);
        } catch (error) {
          console.error('Error receiving WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      setWs(ws);
    };

    connectWebSocket();
  }, []);


  useEffect(() => {
    if (ws) {
      ws.connect();
    }
  }, [ws]);

  if (loading) {
    return (
      <SafeAreaProvider>
        <StatusBar barStyle={mode === 'dark' ? 'dark-content' : 'light-content'} />
        <div className={tailwind('flex items-center justify-center h-screen')}>
          <p className={tailwind('text-xl')}>Loading...</p>
        </div>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar barStyle={mode === 'dark' ? 'dark-content' : 'light-content'} />
      <div className={tailwind('flex h-screen')}>
        {/* Sidebar */}
        <div className={tailwind('bg-gray-800 p-4')}>
          <h2 className={tailwind('text-lg font-bold text-white')}>DeFi Rebalancing Dashboard</h2>
        </div>

        {/* Main Content */}
        <div className={tailwind('flex-grow p-4')}>
          {/* Header */}
          <div className={tailwind('bg-white shadow-md p-4')}>
            <h1 className={tailwind('text-3xl font-bold text-gray-800')}>
              Mossland Strategic Response
            </h1>
            <button
              className={tailwind(
                mode === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-gray-600 hover:bg-gray-200',
                'py-2 px-4 rounded-md mr-2'
              )}
              onClick={() => setMode(mode === 'dark' ? 'light' : 'dark')}
            >
              Toggle Mode
            </button>
          </div>

          {/* Portfolio Overview */}
          <div className={tailwind('mt-4 p-4 rounded-md shadow-md')}>
            <h2 className={tailwind('text-2xl font-bold text-gray-800')}>Portfolio Overview</h2>
            <p className={tailwind('text-gray-600')}>
              Fetching Crypto Data...
            </p>
            {Object.keys(cryptoData).map((asset) => (
              <div key={asset} className={tailwind('mb-2')}>
                <p className={tailwind('text-xl font-bold')}>{asset}</p>
                <p className={tailwind('text-gray-600')}>{cryptoData[asset].price}</p>
              </div>
            ))}
          </div>

          {/* Rebalancing Recommendations */}
          <div className={tailwind('mt-4 p-4 rounded-md shadow-md')}>
            <h2 className={tailwind('text-2xl font-bold text-gray-800')}>
              Rebalancing Recommendations
            </h2>
            {rebalanceRecommendations.length > 0 && (
              <ul className={tailwind('list-disc text-gray-600')}>
                {rebalanceRecommendations.map((recommendation) => (
                  <li key={recommendation.id} className={tailwind('mb-2')}>
                    {recommendation.strategy}
                  </li>
                ))}
              </ul>
            )}
            {!rebalanceRecommendations.length > 0 && (
              <p className={tailwind('text-gray-600')}>
                No recommendations available.
              </p>
            )}
          </div>

          {/* OpenAI Response */}
          <div className={tailwind('mt-4 p-4 rounded-md shadow-md')}>
            <h2 className={tailwind('text-2xl font-bold text-gray-800')}>
              OpenAI Analysis
            </h2>
            <pre className={tailwind('text-gray-600 p-2 rounded-md')}>{openAIResponse}</pre>
          </div>
        </div>
      </div>
    </SafeAreaProvider>
  );
};

export default App;