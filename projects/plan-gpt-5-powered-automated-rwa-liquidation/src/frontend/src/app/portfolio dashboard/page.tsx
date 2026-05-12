import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { Chart } from 'chart.js';

// Define interfaces for data and settings
interface PortfolioHolding {
  symbol: string;
  quantity: number;
  price: number;
}

interface RiskTolerance {
  conservative: number;
  moderate: number;
  aggressive: number;
}

interface PortfolioDashboardProps {
  initialHoldings?: PortfolioHolding[];
  initialRiskTolerance?: RiskTolerance;
}

const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({
  initialHoldings = [],
  initialRiskTolerance = { conservative: 50, moderate: 50, aggressive: 0 },
}) => {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>(initialHoldings);
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance>(initialRiskTolerance);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData>();

  const { search } = useSearchParams();

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate delay
        const simulatedData: PortfolioHolding[] = [
          { symbol: 'BTC', quantity: 10, price: 30000 },
          { symbol: 'ETH', quantity: 5, price: 2000 },
          { symbol: 'BNB', quantity: 20, price: 250 },
        ];
        setHoldings(simulatedData);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch portfolio data.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (!loading && !error) {
      generateChart();
    }
  }, [holdings]);

  const generateChart = () => {
    const ctx = document.getElementById('myChart') as HTMLCanvasElement;
    if (ctx) {
      const data = {
        labels: holdings.map(h => h.symbol),
        datasets: [{
          label: 'Portfolio Value',
          data: holdings.map(h => h.quantity * h.price),
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      };
      new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }
  };

  const handleRiskToleranceChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = parseInt(event.target.value, 10);
    setRiskTolerance({
      ...riskTolerance,
      [event.target.name]: value,
    });
  };

  if (loading) {
    return <div>Loading portfolio data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Portfolio Dashboard</h2>

      <div className="mb-4">
        <p className="text-gray-700">Current Holdings:</p>
        <ul className="space-y-2">
          {holdings.map((holding) => (
            <li key={holding.symbol} className="flex items-center space-x-2">
              <span>{holding.symbol}</span>
              <span className="font-semibold">{holding.quantity}</span>
              <span className="text-gray-600">${holding.price}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Risk Tolerance:</p>
        <div className="flex items-center space-x-4">
          <label className="text-gray-600">Conservative:</label>
          <input
            type="range"
            min="0"
            max="100"
            value={riskTolerance.conservative}
            onChange={(e) => handleRiskToleranceChange(e)}
            className="w-full h-4 bg-gray-200 rounded"
            aria-label="Conservative Risk Tolerance"
          />
          <span className="text-gray-600">{riskTolerance.conservative}%</span>
        </div>
        <div className="flex items-center space-x-4">
          <label className="text-gray-600">Moderate:</label>
          <input
            type="range"
            min="0"
            max="100"
            value={riskTolerance.moderate}
            onChange={(e) => handleRiskToleranceChange(e)}
            className="w-full h-4 bg-gray-200 rounded"
            aria-label="Moderate Risk Tolerance"
          />
          <span className="text-gray-600">{riskTolerance.moderate}%</span>
        </div>
        <div className="flex items-center space-x-4">
          <label className="text-gray-600">Aggressive:</label>
          <input
            type="range"
            min="0"
            max="100"
            value={riskTolerance.aggressive}
            onChange={(e) => handleRiskToleranceChange(e)}
            className="w-full h-4 bg-gray-200 rounded"
            aria-label="Aggressive Risk Tolerance"
          />
          <span className="text-gray-600">{riskTolerance.aggressive}%</span>
        </div>
      </div>

      <canvas id="myChart" width={400} height={200}></canvas>
    </div>
  );
};

interface ChartData {
  labels: string[];
  datasets: any[];
}

export default PortfolioDashboard;