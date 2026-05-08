import React, { useState, useEffect } from 'react';
import { Chart, Line } from 'react-chartjs-2';
import axios from 'axios';

interface PortfolioData {
  nftHoldings: NFTHolding[];
  riskAssessment: RiskAssessment;
}

interface NFTHolding {
  tokenId: string;
  name: string;
  quantity: number;
  value: number;
}

interface RiskAssessment {
  overallRiskScore: number;
  volatility: number;
  liquidity: number;
  correlation: number;
}

const PortfolioDashboard: React.FC = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get<PortfolioData>('https://api.example.com/portfolio-data'); // Replace with your API endpoint
        setPortfolioData(response.data);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch portfolio data');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!portfolioData) {
    return <div>No portfolio data available.</div>;
  }

  const nftHoldings = portfolioData.nftHoldings;
  const riskAssessment = portfolioData.riskAssessment;

  const chartData = {
    labels: nftHoldings.map((holding) => holding.tokenId),
    datasets: [
      {
        label: 'Value',
        data: nftHoldings.map((holding) => holding.value),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: {
          low: 'rgb(255, 99, 132)',
          high: 'rgb(54, 162, 235)',
        },
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    scales: {
      x: {
        title: {
          display: true,
          text: 'NFT Token ID',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Value',
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* NFT Holdings */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">NFT Holdings</h2>
        <ul className="space-y-2">
          {nftHoldings.map((holding) => (
            <li
              key={holding.tokenId}
              aria-label={`NFT Holding: ${holding.name}`}
              className="p-4 border rounded shadow-md"
            >
              <p className="font-semibold mb-1">Token ID: {holding.tokenId}</p>
              <p className="font-semibold mb-1">Name: {holding.name}</p>
              <p className="font-semibold mb-1">Quantity: {holding.quantity}</p>
              <p className="font-semibold mb-1">Value: ${holding.value}</p>
            </li>
          ))}
        </ul>
      </div>

      {/* Risk Assessment */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Risk Assessment</h2>
        <p className="font-semibold">Overall Risk Score: {riskAssessment.overallRiskScore}</p>
        <p className="font-semibold">Volatility: {riskAssessment.volatility}</p>
        <p className="font-semibold">Liquidity: {riskAssessment.liquidity}</p>
        <p className="font-semibold">Correlation: {riskAssessment.correlation}</p>
      </div>

      {/* Interactive Chart */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">NFT Value Chart</h2>
        <Chart
          data={chartData}
          options={chartOptions}
          width={600}
        />
      </div>
    </div>
  );
};

export default PortfolioDashboard;