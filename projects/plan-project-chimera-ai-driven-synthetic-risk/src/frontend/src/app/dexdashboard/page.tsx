import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart } from 'chart.js';

interface RiskScore {
  contractAddress: string;
  riskScore: number;
  count: number;
}

interface DEXDashboardProps {
  initialContractAddresses?: string[];
}

const DEXDashboard: React.FC = ({ initialContractAddresses = [] }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const contractAddressParam = searchParams.get('contractAddress');
  const [contractAddresses, setContractAddresses] = useState<string[]>(initialContractAddresses);
  const [riskScores, setRiskScores] = useState<RiskScore[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData>({ labels: [], data: [] });

  useEffect(() => {
    const contractAddress = contractAddressParam;
    if (contractAddress) {
      setSearchParams({ contractAddress });
    } else {
      setSearchParams({});
    }
  }, [contractAddressParam]);

  useEffect(() => {
    const fetchRiskScores = async () => {
      try {
        const data = await fetch('/api/riskScores'); // Replace with your API endpoint
        const result = await data.json();
        setRiskScores(result);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch risk scores. Please try again.');
        setLoading(false);
      }
    };

    fetchRiskScores();
  }, []);

  useEffect(() => {
    if (!contractAddresses || contractAddresses.length === 0) {
      setChartData({ labels: [], data: [] });
      return;
    }

    const labels = contractAddresses;
    const data = contractAddresses.map(address => riskScores.find(score => score.contractAddress === address)?.count || 0);

    setChartData({ labels, data });
  }, [contractAddresses, riskScores]);


  const renderRiskScoreDistribution = () => {
    if (riskScores.length === 0) return <p>No risk scores available.</p>;

    const labels = riskScores.map(score => score.contractAddress);
    const data = riskScores.map(score => score.count);

    return (
      <div className="grid grid-cols-3 gap-4">
        {riskScores.map((score, index) => (
          <div
            key={index}
            className="bg-gray-100 p-4 rounded-md shadow-md text-center"
            aria-label={`Risk score for ${score.contractAddress}`}
          >
            <p className="font-bold">{score.contractAddress}</p>
            <p>{score.count}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      {loading && <p>Loading risk scores...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {/* Filter by Contract Address */}
      <div className="mb-4">
        <label className="text-sm font-medium text-gray-700" htmlFor="contractAddress">
          Contract Address:
        </label>
        <input
          type="text"
          id="contractAddress"
          className="mt-1 focus:outline-gray-200 border border-gray-300 rounded-md py-2 px-3 w-full"
          placeholder="Enter contract address"
          value={contractAddressParam || ''}
          onChange={(e) => {
            setSearchParams({ contractAddress: e.target.value });
          }}
        />
      </div>

      {/* Risk Score Distribution */}
      <div className="mb-4">
        <h2 className="text-xl font-bold">Risk Score Distribution</h2>
        {renderRiskScoreDistribution()}
      </div>

      {/* Transaction History Visualization */}
      <div className="mb-4">
        <h2 className="text-xl font-bold">Transaction History</h2>
        {chartData.labels.length > 0 ? (
          <canvas
            id="transactionChart"
            width="400"
            height="200"
            className="rounded-md"
          ></canvas>
        ) : (
          <p>No transaction history available.</p>
        )}
      </div>
    </div>
  );
};

interface ChartData {
  labels: string[];
  data: number[];
}

export default DEXDashboard;