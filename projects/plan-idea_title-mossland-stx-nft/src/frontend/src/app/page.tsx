import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { useSearchParams } from 'react-router-dom';
import { Stacks } from 'stacks-js';

type NFTFraction = {
  tokenId: string;
  name: string;
  description: string;
  price: number;
  owner: string;
  metadata: any;
};

type RiskProfile = 'low' | 'medium' | 'high';

type AppState = {
  nftFraction: NFTFraction | null;
  riskProfile: RiskProfile | null;
  isLoading: boolean;
  error: string | null;
};

const Tailwind = useTailwind({
  theme: {
    extend: {
      colors: {
        'mossland-primary': '#2196F3',
        'mossland-secondary': '#FFC107',
      },
    },
  },
});

const App: React.FC<AppState> = () => {
  const [nftFraction, setNftFraction] = useState<NFTFraction | null>(null);
  const [riskProfile, setRiskProfile] = useState<RiskProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const params = useSearchParams();
  const tokenId = params.get('tokenId') || null;

  useEffect(() => {
    const fetchNftFraction = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Simulate fetching data
        const data = {
          tokenId: tokenId || '0x123',
          name: 'Genesis Block NFT',
          description: 'A fractionalized piece of the Genesis Block.',
          price: 100,
          owner: '0x456',
          metadata: {
            name: 'Genesis Block NFT',
            description: 'A fractionalized piece of the Genesis Block.',
            image: 'https://example.com/genesis.png',
          },
        };
        setNftFraction(data);
      } catch (err) {
        setError('Failed to fetch NFT fraction.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchNftFraction();
  }, [tokenId]);

  return (
    <div className={Tailwind.container}>
      <header className={Tailwind.header}>
        <h1>Mossland STX NFT Dashboard</h1>
      </header>

      <main className={Tailwind.main}>
        {isLoading && <p>Loading...</p>}
        {error && <p className="text-red-500">{error}</p>}

        {nftFraction && (
          <div className={Tailwind.card}>
            <h2>{nftFraction.name}</h2>
            <p>Token ID: {nftFraction.tokenId}</p>
            <p>Price: ${nftFraction.price}</p>
            <p>Owner: {nftFraction.owner}</p>
            <p>Description: {nftFraction.description}</p>
            {/* Placeholder for metadata display */}
            <img src={nftFraction.metadata?.image} alt={nftFraction.name} />
            {/* Add more details here */}
          </div>
        )}
      </main>
    </div>
  );
};

export default App;