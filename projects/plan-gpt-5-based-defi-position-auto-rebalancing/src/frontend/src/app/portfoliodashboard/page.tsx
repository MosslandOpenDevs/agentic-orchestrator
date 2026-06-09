import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface PortfolioHolding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  totalValue: number;
}

interface PortfolioProps {
  holdings: PortfolioHolding[];
  performanceData: { [key: string]: number }; // Key: Symbol, Value: Performance Data
}

const PortfolioDashboard: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbol = searchParams.get('symbol');

  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [performanceData, setPerformanceData] = useState<PortfolioProps['performanceData']>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data
    const fetchData = async () => {
      try {
        const data = await fetchPortfolioData();
        setHoldings(data.holdings);
        setPerformanceData(data.performanceData);
        setIsLoading(false);
      } catch (err) {
        setError(err.message || 'Failed to fetch portfolio data');
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const fetchPortfolioData = async () => {
    // Replace with your actual data fetching logic
    const dummyData = [
      { symbol: 'AAPL', name: 'Apple Inc.', quantity: 100, price: 170.34, totalValue: 17034 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', quantity: 50, price: 330.12, totalValue: 16506 },
      { symbol: 'GOOG', name: 'Alphabet Inc.', quantity: 25, price: 2500.00, totalValue: 62500 },
    ];

    const performanceData = {
      AAPL: 1.2,
      MSFT: 0.8,
      GOOG: 1.5,
    };

    return { holdings: dummyData, performanceData };
  };

  if (isLoading) {
    return <div>Loading portfolio...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Portfolio Overview</h1>

      {/* Display Portfolio Holdings */}
      <table className="table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Total Value</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.symbol}>
              <td>{holding.symbol}</td>
              <td>{holding.name}</td>
              <td>{holding.quantity}</td>
              <td>${holding.price.toFixed(2)}</td>
              <td>${holding.totalValue.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Show Portfolio Performance */}
      <div className="mt-4">
        <h2 className="text-xl font-bold mb-2">Performance</h2>
        <p className="text-gray-700">
          AAPL: {performanceData.AAPL ? performanceData.AAPL.toFixed(2) : 'N/A'}
        </p>
        <p className="text-gray-700">
          MSFT: {performanceData.MSFT ? performanceData.MSFT.toFixed(2) : 'N/A'}
        </p>
        <p className="text-gray-700">
          GOOG: {performanceData.GOOG ? performanceData.GOOG.toFixed(2) : 'N/A'}
        </p>
      </div>

      {/* Allow Risk Profile Adjustment (Placeholder) */}
      <div className="mt-4">
        <p className="text-gray-700">
          Risk profile adjustment coming soon!
        </p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;