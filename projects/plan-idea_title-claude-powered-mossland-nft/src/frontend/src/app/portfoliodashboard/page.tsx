import React, { useState, useEffect } from 'react';
import { LineChart, PieChart, BarChart } from 'react-div-charts';
import { useSearchParams } from 'next/script';

interface PortfolioData {
  totalValue: number;
  assets: {
    [key: string]: {
      name: string;
      quantity: number;
      price: number;
      value: number;
    };
  };
  performance: {
    startDate: string;
    endDate: string;
    growth: number;
  };
}

interface PortfolioDashboardProps {
  initialData?: PortfolioData;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({ initialData }) => {
  const [data, setData] = useState<PortfolioData | null>(initialData || null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const startDate = searchParams.get('startDate');
    const endDate = searchParams.get('endDate');

    // Simulate fetching data (replace with actual API call)
    const fetchData = async () => {
      try {
        const simulatedData: PortfolioData = {
          totalValue: 100000,
          assets: {
            'BTC': { name: 'Bitcoin', quantity: 10, price: 30000, value: 300000 },
            'ETH': { name: 'Ethereum', quantity: 5, price: 2000, value: 10000 },
            'USDT': { name: 'Tether', quantity: 100, price: 1, value: 100000 },
          },
          performance: {
            startDate: startDate || '2023-01-01',
            endDate: endDate || '2024-01-01',
            growth: 1.5,
          },
        };
        setData(simulatedData);
        setLoading(false);
        setError(null);
      } catch (err) {
        setError('Failed to fetch portfolio data.');
        setLoading(false);
      }
    };

    fetchData();
  }, [searchParams]);

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data) {
    return <div>No portfolio data available.</div>;
  }

  const assetNames = Object.keys(data.assets);

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Portfolio Overview</h2>

      <section className="mb-6">
        <p className="text-gray-700">Total Portfolio Value: ${data.totalValue.toFixed(2)}</p>
      </section>

      <section className="mb-6">
        <h3>Asset Allocation</h3>
        <div className="flex flex-col md:flex-row">
          <PieChart
            data={[
              { name: assetNames[0], value: data.assets[assetNames[0]].value },
              { name: assetNames[1], value: data.assets[assetNames[1]].value },
              { name: assetNames[2], value: data.assets[assetNames[2]].value },
            ]}
            className="w-full md:w-1/2"
          />
          <div className="w-full md:w-1/2 p-4">
            <p className="text-gray-700 mb-2">Asset Breakdown:</p>
            <ul>
              {assetNames.map((asset) => (
                <li key={asset}>
                  {data.assets[asset].name}: ${data.assets[asset].value.toFixed(2)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-6">
        <h3>Performance Metrics</h3>
        <p className="text-gray-700">
          Start Date: {data.performance.startDate}, End Date: {data.performance.endDate}, Growth: {data.performance.growth * 100} %
        </p>
      </section>

      <section className="mb-6">
        <h3>Performance Chart</h3>
        <BarChart
          data={[
            { x: data.performance.startDate, y: 0 },
            { x: data.performance.endDate, y: data.performance.growth },
          ]}
          className="w-full"
        />
      </section>
    </div>
  );
};

export default PortfolioDashboard;