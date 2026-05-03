import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';
import { ethers } from 'ethers';
import { useDebounce } from 'react-use';

// Placeholder data - replace with actual data fetching
interface StablecoinData {
  name: string;
  riskScore: number;
  transactionHistory: string[];
}

const initialStablecoins: StablecoinData[] = [
  { name: 'USDC', riskScore: 5, transactionHistory: ['Transaction 1', 'Transaction 2'] },
  { name: 'DAI', riskScore: 8, transactionHistory: ['Transaction 3', 'Transaction 4'] },
  { name: 'LTC', riskScore: 2, transactionHistory: ['Transaction 5', 'Transaction 6'] },
];

const Dashboard: React.FC = () => {
  const [stablecoins, setStablecoins] = useState<StablecoinData[]>(initialStablecoins);
  const [selectedStablecoin, setSelectedStablecoin] = useState<string | null>(null);
  const [riskScoreChartData, setRiskScoreChartData] = useState<number[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Debounce the updateStablecoins function
  const debouncedUpdateStablecoins = useDebounce((newStablecoins: StablecoinData[]) => {
    setStablecoins(newStablecoins);
  }, 500);

  useEffect(() => {
    // Simulate fetching data from external sources
    setTimeout(() => {
      setLoading(false);
      debouncedUpdateStablecoins(stablecoins);
    }, 1000);
  }, []);

  const handleStablecoinSelect = (stablecoinName: string) => {
    setSelectedStablecoin(stablecoinName);
  };

  const handleRiskScoreChange = (index: number) => {
    const updatedStablecoins = [...stablecoins];
    updatedStablecoins[index].riskScore = 5; // Example update
    debouncedUpdateStablecoins(updatedStablecoins);
  };

  const generateRiskScoreChartData = () => {
    return stablecoins.map(sc => sc.riskScore);
  };

  useEffect(() => {
    setRiskScoreChartData(generateRiskScoreChartData());
  }, [stablecoins]);

  return (
    <div className="bg-gray-100 min-h-screen p-4">
      <header className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <h1>Real-time Stablecoin Authenticity Verification</h1>
        <nav>
          <button onClick={() => handleStablecoinSelect('USDC')} className="bg-gray-600 text-white px-2 py-1 rounded">USDC</button>
          <button onClick={() => handleStablecoinSelect('DAI')} className="bg-gray-600 text-white px-2 py-1 rounded">DAI</button>
          <button onClick={() => handleStablecoinSelect('LTC')} className="bg-gray-600 text-white px-2 py-1 rounded">LTC</button>
        </nav>
      </header>

      <main className="mt-4">
        {loading ? (
          <div className="text-center p-4">
            <p>Loading data...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Stablecoin Cards */}
            {stablecoins.map((stablecoin, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg"
              >
                <h2 className="text-lg font-bold">{stablecoin.name}</h2>
                <p className="text-gray-700">Risk Score: {stablecoin.riskScore}</p>
                <p className="text-gray-700">Transaction History: {stablecoin.transactionHistory.join(', ')}</p>
                <button onClick={() => handleRiskScoreChange(index)} className="bg-blue-500 text-white px-2 py-1 rounded mt-2">
                  Update Risk Score
                </button>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer className="bg-gray-800 text-white p-4">
        <RiskScoreChart data={riskScoreChartData} />
      </footer>
    </div>
  );
};

const RiskScoreChart = ({ data }) => {
  const chartRef = React.useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (chartRef.current) {
      const ctx = chartRef.current.getContext('2d');
      if (ctx) {
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            datasets: [{
              label: 'Risk Scores',
              data: data,
              borderColor: 'rgb(75, 192, 192)',
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        });
      }
    }
  }, [data]);

  return <canvas ref={chartRef} width="400" height="200"></canvas>;
};

export default Dashboard;