import React, { useState, useEffect } from 'react';
import { useServerApi } from '../../api/useServerApi'; // Assuming API wrapper exists
import { PortfolioHolding } from '../../types/portfolio'; // Assuming portfolio type definition
import { LineChart, BarChart, Tooltip, XAxis, YAxis } from 'react-div-chart';

interface PortfolioOverviewProps {
  userId: string;
}

const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ userId }) => {
  const [holdings, setHoldings] = useState<PortfolioHolding[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const api = useServerApi();

  useEffect(() => {
    const fetchHoldings = async () => {
      setLoading(true);
      try {
        const data = await api.getPortfolioHoldings(userId);
        if (data) {
          setHoldings(data);
        } else {
          setError('Failed to fetch portfolio holdings.');
        }
      } catch (err: any) {
        setError(err.message || 'An error occurred.');
      } finally {
        setLoading(false);
      }
    };

    fetchHoldings();
  }, [userId, api]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md text-center">
        Loading portfolio...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md text-center">
        Error: {error}
      </div>
    );
  }

  if (!holdings) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md text-center">
        No portfolio data available.
      </div>
    );
  }

  const totalPortfolioValue = holdings.reduce((sum, holding) => sum + holding.value, 0);

  // Risk Assessment Visualization (Simplified Example)
  const riskScore = holdings.reduce((sum, holding) => sum + holding.riskScore, 0);

  return (
    <div className="bg-white p-4 rounded-md shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Portfolio Overview</h2>

      <div className="grid grid-cols-1 gap-4">
        <div className="col-span-2">
          <h3>Portfolio Holdings</h3>
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Quantity</th>
                <th>Value</th>
                <th>Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding) => (
                <tr key={holding.id}>
                  <td>{holding.asset}</td>
                  <td>{holding.quantity}</td>
                  <td>${holding.value.toFixed(2)}</td>
                  <td>{holding.riskScore}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="col-span-1">
          <h3>Total Portfolio Value</h3>
          <p className="text-xl font-bold">${totalPortfolioValue.toFixed(2)}</p>
        </div>
      </div>

      <div className="mt-4 mb-4">
        <h3>Risk Assessment</h3>
        <p>Total Risk Score: {riskScore}</p>
      </div>

      <div className="mt-4">
        <h3>Risk Visualization</h3>
        <LineChart
          data={[
            { x: 'Time', y: [riskScore] },
          ]}
          width={400}
          height={200}
          className="mt-2"
          aria-label="Risk Assessment Over Time"
        />
      </div>
    </div>
  );
};

export default PortfolioOverview;