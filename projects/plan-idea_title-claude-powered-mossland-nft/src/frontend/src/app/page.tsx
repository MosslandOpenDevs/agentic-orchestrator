import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { CoinGecko } from './api/CoinGecko';
import { WebSocketClient } from './api/WebSocketClient';

const Tailwind = useTailwind();

type PortfolioItem = {
  tokenId: string;
  name: string;
  quantity: number;
  price: number;
  floorPrice: number;
  imageUrl: string;
};

type PortfolioData = {
  assets: PortfolioItem[];
  totalValue: number;
};

const PortfolioDashboard: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData>({
    assets: [],
    totalValue: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        const cryptoPrices = await CoinGecko.getPrices(['MOSSLAND']);
        const ws = new WebSocketClient();
        ws.onopen = () => {
          console.log('WebSocket connected');
        };
        ws.onmessage = async (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
            // Update portfolio data based on WebSocket messages
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        const assets: PortfolioItem[] = [
          { tokenId: '123', name: 'Mossland NFT 1', quantity: 5, price: cryptoPrices.MOSSLAND.price * 5, floorPrice: 100, imageUrl: 'https://example.com/mossland1.png' },
          { tokenId: '456', name: 'Mossland NFT 2', quantity: 10, price: cryptoPrices.MOSSLAND.price * 10, floorPrice: 150, imageUrl: 'https://example.com/mossland2.png' },
        ];
        setPortfolioData({ assets, totalValue: assets.reduce((acc, asset) => acc + asset.quantity * asset.price, 0) });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching portfolio data:', error);
        setLoading(false);
      }
    };

    fetchPortfolioData();
  }, []);

  if (loading) {
    return (
      <div className={darkMode ? Tailwind.container.fill('gray') : Tailwind.container.fill('white')}>
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  return (
    <div className={darkMode ? Tailwind.container.fill('black') : Tailwind.container.fill('white')}>
      <header className={Tailwind.header.fill('bg-gray-800')}>
        <h1 className={Tailwind.header.text.fill('white')}>Claude-Powered Portfolio</h1>
        <button onClick={() => setDarkMode(!darkMode)}>Toggle Dark Mode</button>
      </header>

      <main className={Tailwind.main.fill('bg-white')}>
        <section className={Tailwind.section.fill('p-4')}>
          <h2 className={Tailwind.section.heading.fill('text-xl font-bold')}>Portfolio Overview</h2>
          {portfolioData.assets.map((asset) => (
            <div key={asset.tokenId} className={Tailwind.card.fill('bg-gray-100 p-4 rounded-md')}>
              <img src={asset.imageUrl} alt={asset.name} className={Tailwind.card.image.fill('w-16 h-16 rounded-md')}/>
              <p className={Tailwind.card.title.fill('text-lg font-bold')}>
                {asset.name} ({asset.tokenId})
              </p>
              <p className={Tailwind.card.quantity.fill('text-gray-600')}>
                Quantity: {asset.quantity}
              </p>
              <p className={Tailwind.card.price.fill('text-gray-600')}>
                Price: ${asset.price.toFixed(2)}
              </p>
              <p className={Tailwind.card.floorPrice.fill('text-gray-600')}>
                Floor Price: ${asset.floorPrice.toFixed(2)}
              </p>
            </div>
          ))}
          <p className={Tailwind.card.totalValue.fill('text-xl font-bold mt-4')}>
            Total Value: ${portfolioData.totalValue.toFixed(2)}
          </p>
        </section>
      </main>
    </div>
  );
};

export default PortfolioDashboard;

// api/CoinGecko.ts
import { CoinGeckoClient } from 'coin-gecko-api';

const coinGecko = new CoinGeckoClient();

export const CoinGeckoApi = {
  getPrices: async (symbol: string[]): Promise<{ [symbol: string]: { price: number } }> => {
    try {
      const response = await coinGecko.getPrices(symbol);
      return response;
    } catch (error) {
      console.error('Error fetching prices from CoinGecko:', error);
      throw error;
    }
  },
};

// api/WebSocketClient.ts
import { WebSocket } from 'ws';

export class WebSocketClient {
  private ws: WebSocket | null = null;

  onopen: (event: Event) => void = () => {};
  onmessage: (event: MessageEvent) => void = () => {};
  onerror: (event: ErrorEvent) => void = () => {};

  connect = async (url: string) => {
    this.ws = new WebSocket(url);

    this.ws.onopen = (event) => {
      this.onopen(event);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onmessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (event) => {
      this.onerror(event);
    };
  };

  close = () => {
    if (this.ws) {
      this.ws.close();
    }
  };
}