import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';
import { useSearchParams } from 'next/searchparams';

interface CollateralData {
  btc: number;
  eth: number;
  ltc: number;
  // Add more assets as needed
}

interface DashboardProps {
  initialData?: CollateralData;
}

const CollateralDashboard: React.FC<DashboardProps> = ({ initialData = {} }) => {
  const [data, setData] = useState<CollateralData>(initialData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [treasuryRatio, setTreasuryRatio] = useState<number>(50); // Initial value
  const [btcRatio, setBtcRatio] = useState<number>(50);
  const [ethRatio, setEthRatio] = useState<number>(50);
  const [ltcRatio, setLtcRatio] = useState<number>(50);

  const searchParams = useSearchParams();
  const updateTreasuryRatio = (value: number) => {
    setTreasuryRatio(value);
  };

  const updateBtcRatio = (value: number) => {
    setBtcRatio(value);
  };

  const updateEthRatio = (value: number) => {
    setEthRatio(value);
  };

  const updateLtcRatio = (value: number) => {
    setLtcRatio(value);
  };

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    const fetchData = async () => {
      try {
        const btc = Math.random() * 100;
        const eth = Math.random() * 100;
        const ltc = Math.random() * 100;

        setData({ btc, eth, ltc });
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const chartData = {
    labels: ['Last Update'],
    datasets: [
      {
        label: 'Collateral Ratio',
        data: [treasuryRatio, btcRatio, ethRatio, ltcRatio],
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-3xl font-bold mb-4">Collateral Dashboard</h1>

      <div className="w-full md:w-2/3">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} options={chartOptions} className="mt-4" />
        </ResponsiveContainer>
      </div>

      <div className="w-full md:w-2/3 mt-4">
        <p className="text-lg mb-2">Treasury Ratio: <input
          type="range"
          min="0"
          max="100"
          value={treasuryRatio}
          onChange={(e) => updateTreasuryRatio(Number(e.target.value))}
          aria-label="Treasury Ratio"
          className="w-full h-3"
        /> {treasuryRatio}%</p>
        <p className="text-lg mb-2">BTC Ratio: <input
          type="range"
          min="0"
          max="100"
          value={btcRatio}
          onChange={(e) => updateBtcRatio(Number(e.target.value))}
          aria-label="BTC Ratio"
          className="w-full h-3"
        /> {btcRatio}%</p>
        <p className="text-lg mb-2">ETH Ratio: <input
          type="range"
          min="0"
          max="100"
          value={ethRatio}
          onChange={(e) => updateEthRatio(Number(e.target.value))}
          aria-label="ETH Ratio"
          className="w-full h-3"
        /> {ethRatio}%</p>
        <p className="text-lg mb-2">LTC Ratio: <input
          type="range"
          min="0"
          max="100"
          value={ltcRatio}
          onChange={(e) => updateLtcRatio(Number(e.target.value))}
          aria-label="LTC Ratio"
          className="w-full h-3"
        /> {ltcRatio}%</p>
      </div>
    </div>
  );
};

export default CollateralDashboard;