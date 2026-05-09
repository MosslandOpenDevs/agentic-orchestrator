import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoingeckoAPI } from './api/coingecko';
import { OpenAIAPI } from './api/openai';
import { WebSocketClient } from './api/websocket';
import { PortfolioData } from './types/portfolio';
import { AssetData } from './types/asset';

const Tailwind = useTailwind();

type PortfolioState = {
  holdings: PortfolioData[],
  riskTolerance: number;
  timeHorizon: number;
  gptRecommendations: string | null;
  loading: boolean;
  error: string | null;
};

const PortfolioDashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData[]>([]);
  const [riskTolerance, setRiskTolerance] = useState(50);
  const [timeHorizon, setTimeHorizon] = useState(1);
  const [gptRecommendations, setGptRecommendations] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const cryptoData = await CoingeckoAPI.getAssets();
        const initialHoldings: PortfolioData[] = cryptoData.map(
          asset => ({
            tokenId: asset.id,
            name: asset.name,
            quantity: 0,
            price: 0,
            lastUpdated: new Date()
          })
        );
        setPortfolio(initialHoldings);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch initial data.');
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  useEffect(() => {
    if (!portfolio || portfolio.length === 0) return;

    const analyzePortfolio = async () => {
      setLoading(true);
      setError(null);

      try {
        const prompt = `Analyze the following NFT portfolio: ${JSON.stringify(portfolio)}.  Assess risk and suggest yield optimization strategies.  Consider a risk tolerance of ${riskTolerance}% and a time horizon of ${timeHorizon} years.`;
        const response = await OpenAIAPI.createCompletion(prompt);
        setGptRecommendations(response.choices[0].text);
      } catch (err) {
        setError('Failed to analyze portfolio with GPT-5.');
      } finally {
        setLoading(false);
      }
    };

    analyzePortfolio();
  }, [portfolio, riskTolerance, timeHorizon]);

  return (
    <div className={Tailwind('bg-gray-100 p-4')}>
      <header className={Tailwind('bg-gray-50 shadow-md p-4')}>
        <h1 className={Tailwind('text-2xl font-bold text-gray-800')}>
          Mossland MAPA Dashboard
        </h1>
      </header>

      <main className={Tailwind('max-w-4xl mx-auto p-4')}>
        {loading && (
          <div className={Tailwind('text-center mt-4')}>
            <p>Loading portfolio data...</p>
          </div>
        )}
        {error && (
          <div className={Tailwind('text-red-500 p-4')}>
            <p>Error: {error}</p>
          </div>
        )}

        {gptRecommendations && (
          <div className={Tailwind('mt-4')}>
            <p className={Tailwind('text-gray-700')}>GPT-5 Recommendations:</p>
            <pre className={Tailwind('p-4 bg-white rounded shadow-sm')}>{gptRecommendations}</pre>
          </div>
        )}

        {/* Portfolio Display */}
        <div className={Tailwind('mt-6')}>
          <h2 className={Tailwind('text-xl font-bold text-gray-800')}>Portfolio Holdings</h2>
          <table className={Tailwind('table-auto border-collapse')}>
            <thead>
              <tr className={Tailwind('text-center bg-gray-100')}>
                <th className={Tailwind('px-4 py-2')}>Token ID</th>
                <th className={Tailwind('px-4 py-2')}>Name</th>
                <th className={Tailwind('px-4 py-2')}>Quantity</th>
                <th className={Tailwind('px-4 py-2')}>Price</th>
                <th className={Tailwind('px-4 py-2')}>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map(holding => (
                <tr key={holding.tokenId} className={Tailwind('text-center')}>
                  <td className={Tailwind('px-4 py-2')}>{holding.tokenId}</td>
                  <td className={Tailwind('px-4 py-2')}>{holding.name}</td>
                  <td className={Tailwind('px-4 py-2')}>{holding.quantity}</td>
                  <td className={Tailwind('px-4 py-2')}>{holding.price}</td>
                  <td className={Tailwind('px-4 py-2')}>{holding.lastUpdated.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
};

export default PortfolioDashboard;