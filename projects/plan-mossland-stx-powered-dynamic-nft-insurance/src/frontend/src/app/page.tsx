import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { useSearchParams } from 'react-router-dom';
import { Stacks } from 'stacks-js';

// Mock data (replace with actual data fetching)
interface NFTFraction {
  tokenId: string;
  fractionPercentage: number;
  price: number;
  metadata: any;
}

interface UserRiskProfile {
  riskLevel: 'low' | 'medium' | 'high';
  investmentHorizon: 'short' | 'medium' | 'long';
}

type PortfolioData = {
  nftFractions: NFTFraction[];
  totalPortfolioValue: number;
};

type AppState = {
  portfolio: PortfolioData;
  loading: boolean;
  riskProfile: UserRiskProfile | null;
};

const App: React.FC = () => {
  const [tailwind] = useTailwind();
  const [searchParams] = useSearchParams();
  const nftFractionId = searchParams.get('nftFractionId');

  const [appState, setAppState] = useState<AppState>({
    portfolio: {
      nftFractions: [],
      totalPortfolioValue: 0,
    },
    loading: true,
    riskProfile: null,
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        // Simulate fetching data
        await new Promise((resolve) => setTimeout(resolve, 1500)); // Simulate API delay

        const portfolioData: PortfolioData = {
          nftFractions: [
            { tokenId: 'NFT1', fractionPercentage: 0.5, price: 1000, metadata: {} },
            { tokenId: 'NFT2', fractionPercentage: 0.25, price: 500, metadata: {} },
          ],
          totalPortfolioValue: 1750,
        };

        const riskProfile: UserRiskProfile = { riskLevel: 'medium', investmentHorizon: 'medium' };

        setAppState({
          portfolio: portfolioData,
          loading: false,
          riskProfile: riskProfile,
        });
      } catch (error) {
        console.error('Error loading data:', error);
        setAppState({
          portfolio: { nftFractions: [], totalPortfolioValue: 0 },
          loading: false,
          riskProfile: null,
        });
      }
    };

    loadData();
  }, []);

  if (appState.loading) {
    return (
      <div className={tailwind('flex items-center justify-center h-screen')}>
        <p className={tailwind('text-xl')}>Loading...</p>
      </div>
    );
  }

  return (
    <div className={tailwind('min-h-screen bg-gray-100')}>
      <header className={tailwind('bg-white shadow-md p-4')}>
        <h1 className={tailwind('text-2xl font-bold text-gray-800')}>Mossland STX Dashboard</h1>
      </header>

      <main className={tailwind('p-4')}>
        {/* Portfolio Overview */}
        <div className={tailwind('mb-4 rounded-lg shadow-md bg-white')}>
          <h2 className={tailwind('text-xl font-bold mb-2')}>Portfolio Value</h2>
          <p className={tailwind('text-gray-700 font-semibold')}>
            Total Portfolio Value: ${appState.portfolio.totalPortfolioValue}
          </p>
        </div>

        {/* NFT Fraction Details */}
        {nftFractionId ? (
          <NFTFractionDetails
            tokenId={nftFractionId}
            fractionPercentage={appState.portfolio.nftFractions.find(
              (f) => f.tokenId === nftFractionId
            )?.fractionPercentage || 0}
            price={appState.portfolio.nftFractions.find(
              (f) => f.tokenId === nftFractionId
            )?.price || 0}
            metadata={appState.portfolio.nftFractions.find(
              (f) => f.tokenId === nftFractionId
            )?.metadata || {}}
          />
        ) : (
          <p className={tailwind('text-center mt-4')}>
            Select an NFT Fraction to view details.
          </p>
        )}
      </main>
    </div>
  );
};

export default App;

// Mock NFTFractionDetails Component
const NFTFractionDetails = ({
  tokenId,
  fractionPercentage,
  price,
  metadata,
}: {
  tokenId: string;
  fractionPercentage: number;
  price: number;
  metadata: any;
}) => {
  return (
    <div className={tailwind('border rounded-lg p-4 shadow-md')}>
      <h3 className={tailwind('text-xl font-bold mb-2')}>NFT Fraction Details</h3>
      <p className={tailwind('text-gray-700 font-semibold')}>
        Token ID: {tokenId}
      </p>
      <p className={tailwind('text-gray-700 font-semibold')}>
        Fraction Percentage: {fractionPercentage}%
      </p>
      <p className={tailwind('text-gray-700 font-semibold')}>
        Price: ${price}
      </p>
      <p className={tailwind('text-gray-700 font-semibold')}>
        Metadata: {JSON.stringify(metadata)}
      </p>
    </div>
  );
};