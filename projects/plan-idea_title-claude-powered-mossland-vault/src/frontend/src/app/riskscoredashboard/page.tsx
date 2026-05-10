import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart, Line } from 'react-chartjs-2';
import { LineElement, Point, TooltipBuilder } from 'chart.js';

interface RiskScoreData {
  walletAddress: string;
  riskScore: number;
  riskScoreHistory: Array<number>;
}

interface RiskScoreDashboardProps {
  initialWalletAddress?: string;
}

const RiskScoreDashboard: React.FC<RiskScoreDashboardProps> = ({ initialWalletAddress }) => {
  const [walletAddress, setWalletAddress] = useState<string>('');
  const [riskScore, setRiskScore] = useState<number>(0);
  const [riskScoreHistory, setRiskScoreHistory] = useState<Array<number> | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<any | null>(null);

  const searchParams = useSearchParams();
  const selectedWalletAddress = searchParams.get('walletAddress') || initialWalletAddress || '';

  useEffect(() => {
    setWalletAddress(selectedWalletAddress);
    setIsLoading(true);
    fetchRiskScoreData();
  }, [selectedWalletAddress]);

  const fetchRiskScoreData = async () => {
    try {
      const response = await fetch(`/api/risk-score?walletAddress=${walletAddress}`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data: RiskScoreData = await response.json();
      setRiskScore(data.riskScore);
      setRiskScoreHistory(data.riskScoreHistory);
      setChartData(createChartData(data.riskScoreHistory));
      setIsLoading(false);
      setError(null);
    } catch (error) {
      setError(`Failed to fetch risk score data: ${error}`);
      setIsLoading(false);
    }
  };

  const createChartData = (history: Array<number> | null) => {
    if (!history || history.length === 0) {
      return null;
    }
    const labels = history.map((_, index) => index);
    const dataPoints = history;

    return {
      labels: labels,
      datasets: [
        {
          label: 'Risk Score',
          data: dataPoints,
          fill: false,
          backgroundColor: 'rgb(255, 99, 132)',
          borderColor: 'rgb(255, 99, 132)',
          tension: 0.1,
        },
      ],
    };
  };

  const chartOptions = {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md">
      {isLoading && (
        <div className="text-center p-4">
          Loading risk score...
        </div>
      )}
      {error && (
        <div className="text-center p-4 text-red-500">
          Error: {error}
        </div>
      )}
      {riskScore > 0 && !isLoading && !error && (
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-2">Risk Score: {riskScore.toFixed(2)}</h2>
          {riskScoreHistory && riskScoreHistory.length > 0 ? (
            <div className="relative">
              <Chart
                data={chartData}
                options={chartOptions}
                height={200}
              />
            </div>
          ) : (
            <p>No risk score history available.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskScoreDashboard;