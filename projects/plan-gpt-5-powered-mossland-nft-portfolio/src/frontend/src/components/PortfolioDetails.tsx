import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface PortfolioDetailsProps {
  portfolioId: string;
}

const PortfolioDetails: React.FC<PortfolioDetailsProps> = ({ portfolioId }) => {
  const [nftAssetAllocation, setNftAssetAllocation] = useState<string | null>(null);
  const [rainBalance, setRainBalance] = useState<string | null>(null);
  const [transactionHistory, setTransactionHistory] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolioData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Simulate fetching data from an API
        const data = await fetchPortfolioDataFromApi(portfolioId);

        if (data) {
          setNftAssetAllocation(data.nftAssetAllocation);
          setRainBalance(data.rainBalance);
          setTransactionHistory(data.transactionHistory);
        } else {
          setError('Failed to fetch portfolio data.');
        }
      } catch (err) {
        setError('An error occurred while fetching portfolio data.');
        console.error('Error fetching portfolio data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPortfolioData();
  }, [portfolioId]);

  const fetchPortfolioDataFromApi = async (id: string) => {
    // Replace with your actual API call
    const response = await fetch(`https://api.example.com/portfolios/${id}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  };

  if (isLoading) {
    return <div>Loading portfolio details...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4 text-gray-800">Portfolio Details</h1>

      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">NFT Asset Allocation</h2>
        <p className="text-gray-700">{nftAssetAllocation || 'Not available'}</p>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">Rain Balance</h2>
        <p className="text-gray-700">{rainBalance || 'Not available'}</p>
      </div>

      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">Transaction History</h2>
        <ul className="list-disc text-gray-700">
          {transactionHistory ? transactionHistory.map((item, index) => (
            <li key={index} aria-label={`Transaction ${index + 1}`}>
              {item}
            </li>
          )) : (
            <li>No transaction history available.</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default PortfolioDetails;