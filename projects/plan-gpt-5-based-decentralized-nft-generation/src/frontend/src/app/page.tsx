import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoinGecko } from './api/CoinGecko'; // Assuming this exists
import { WebSocketClient } from './api/WebSocketClient'; // Assuming this exists

const Dashboard = () => {
  const [tailwind] = useTailwind({});
  const [loading, setLoading] = useState(true);
  const [nftValuations, setNftValuations] = useState<any[]>([]);
  const [cryptoPrices, setCryptoPrices] = useState<any>();
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    const fetchNftValuations = async () => {
      try {
        const valuations = await CoinGecko.getNftValuations();
        setNftValuations(valuations);
      } catch (error) {
        console.error('Error fetching NFT valuations:', error);
      }
    };

    const fetchCryptoPrices = async () => {
      try {
        const prices = await CoinGecko.getCryptoPrices();
        setCryptoPrices(prices);
      } catch (error) {
        console.error('Error fetching crypto prices:', error);
      }
    };

    const connectWebSocket = async () => {
      try {
        await new WebSocketClient().connect();
        setWsConnected(true);
      } catch (error) {
        console.error('Error connecting to WebSocket:', error);
      }
    };

    fetchNftValuations();
    fetchCryptoPrices();
    connectWebSocket();

    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-2xl font-bold')}>DynaNFT Dashboard</p>
        <p className={tailwind('text-gray-400')}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={tailwind('min-h-screen bg-gray-100')}>
      <header className={tailwind('bg-white shadow-md p-4')}>
        <h1 className={tailwind('text-3xl font-bold text-gray-800')}>DynaNFT Dashboard</h1>
      </header>

      <main className={tailwind('p-4')}>
        {/* NFT Valuation Card */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>NFT Valuations</h2>
          {nftValuations.length > 0 ? (
            <ul className={tailwind('list-disc list-inside')}>
              {nftValuations.map((valuation) => (
                <li key={valuation.id} className={tailwind('mb-2')}>
                  {valuation.name} - {valuation.valuation}
                </li>
              ))}
            </ul>
          ) : (
            <p className={tailwind('text-gray-500')}>No NFT valuations available.</p>
          )}
        </div>

        {/* Crypto Price Card */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>Crypto Prices</h2>
          {cryptoPrices ? (
            Object.entries(cryptoPrices).map(([coin, price]) => (
              <p key={coin} className={tailwind('mb-2')}>
                {coin} - {price}
              </p>
            ))
          ) : (
            <p className={tailwind('text-gray-500')}>No crypto prices available.</p>
          )}
        </div>

        {/* Placeholder for Trade Automation Configuration */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white p-4')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>Trade Automation</h2>
          <p className={tailwind('text-gray-500')}>Configure automated trading rules here.</p>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;