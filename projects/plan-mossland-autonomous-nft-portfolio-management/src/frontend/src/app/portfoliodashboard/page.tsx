import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface PortfolioHolding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  totalValue: number;
}

interface RiskAssessment {
  overallRisk: string;
  riskFactors: string[];
}

interface GPT5Recommendation {
  recommendation: string;
  confidence: number;
  rationale: string;
}

const PortfolioDashboard: React.FC = () => {
  const [portfolioHoldings, setPortfolioHoldings] = useState<PortfolioHolding[]>([]);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment>({
    overallRisk: 'Moderate',
    riskFactors: [],
  });
  const [gpt5Recommendation, setGPT5Recommendation] = useState<GPT5Recommendation>({
    recommendation: 'Hold VanEck',
    confidence: 0.6,
    rationale: 'Initial data suggests a potential upside, but further analysis is required.',
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data (replace with actual API calls)
    const fetchData = async () => {
      try {
        const holdingsData: PortfolioHolding[] = [
          { symbol: 'SPY', name: 'SPY ETF', quantity: 100, price: 450, totalValue: 45000 },
          { symbol: 'VNQ', name: 'VNQ REIT', quantity: 50, price: 90, totalValue: 4500 },
          { symbol: 'GLD', name: 'GLD ETF', quantity: 20, price: 180, totalValue: 3600 },
        ];
        setPortfolioHoldings(holdingsData);
        setLoading(false);
      } catch (err) {
        setError('Failed to load portfolio data.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    // Simulate risk assessment (replace with actual risk calculation)
    const calculateRisk = () => {
      setRiskAssessment({
        overallRisk: 'Moderate',
        riskFactors: ['Market Volatility', 'Sector Exposure'],
      });
    };

    calculateRisk();
  }, []);

  useEffect(() => {
    // Simulate GPT-5 recommendation (replace with actual GPT-5 API call)
    const generateRecommendation = () => {
      setGPT5Recommendation({
        recommendation: 'Hold VanEck',
        confidence: 0.6,
        rationale: 'Initial data suggests a potential upside, but further analysis is required.',
      });
    };

    generateRecommendation();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-xl">Loading portfolio data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md">
        <p className="text-xl text-red-700">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md flex flex-col">
      <h1 className="text-3xl font-bold mb-4">Portfolio Dashboard</h1>

      {/* Portfolio Holdings */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-2">Holdings</h2>
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
            {portfolioHoldings.map((holding) => (
              <tr key={holding.symbol} aria-label={`Portfolio holding for ${holding.symbol}`}>
                <td>{holding.symbol}</td>
                <td>{holding.name}</td>
                <td>{holding.quantity}</td>
                <td>${holding.price.toFixed(2)}</td>
                <td>${holding.totalValue.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Risk Assessment */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-2">Risk Assessment</h2>
        <p className="text-gray-700">Overall Risk: {riskAssessment.overallRisk}</p>
        <p className="text-gray-700">Risk Factors: {riskAssessment.riskFactors.join(', ')}</p>
      </div>

      {/* GPT-5 Recommendation */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold mb-2">GPT-5 Recommendation</h2>
        <p className="text-gray-700">Recommendation: {gpt5Recommendation.recommendation}</p>
        <p className="text-gray-700">Confidence: {gpt5Recommendation.confidence.toFixed(2)}</p>
        <p className="text-gray-700">Rationale: {gpt5Recommendation.rationale}</p>
      </div>
    </div>
  );
};

export default PortfolioDashboard;