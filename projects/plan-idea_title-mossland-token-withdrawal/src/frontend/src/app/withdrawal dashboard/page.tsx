import React, { useState, useEffect } from 'react';
import { Chart } from 'chart.js';

interface WithdrawalData {
  nftAddress: string;
  withdrawalId: string;
  status: 'pending' | 'completed' | 'failed';
  timestamp: string;
  amount: number;
}

interface WithdrawalDashboardProps {
  withdrawals: WithdrawalData[];
  onFilterChange: (address: string) => void;
}

const WithdrawalDashboard: React.FC<WithdrawalDashboardProps> = ({ withdrawals, onFilterChange }) => {
  const [filteredWithdrawals, setFilteredWithdrawals] = useState<WithdrawalData[]>(withdrawals);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    // Simulate fetching data (replace with actual API call)
    const fetchData = async () => {
      const data: WithdrawalData[] = [
        { nftAddress: '0x123', withdrawalId: '1', status: 'pending', timestamp: '2024-01-01T10:00:00Z', amount: 1.5 },
        { nftAddress: '0x456', withdrawalId: '2', status: 'completed', timestamp: '2024-01-01T11:00:00Z', amount: 2.0 },
        { nftAddress: '0x123', withdrawalId: '3', status: 'failed', timestamp: '2024-01-01T12:00:00Z', amount: 0.8 },
        { nftAddress: '0x789', withdrawalId: '4', status: 'pending', timestamp: '2024-01-01T13:00:00Z', amount: 1.2 },
      ];
      setFilteredWithdrawals(data);
      setLoading(false);
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (onFilterChange) {
      onFilterChange('0x123'); // Default filter to 0x123
    }
  }, [onFilterChange]);

  if (loading) {
    return <div>Loading withdrawals...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const chartData = {
    labels: filteredWithdrawals.map(w => w.timestamp),
    datasets: [
      {
        label: 'Withdrawal Status',
        data: filteredWithdrawals.map(w => w.status.length),
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          display: false,
        },
      },
    },
  };

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">NFT Withdrawal Dashboard</h2>

      {/* Filter by NFT Address */}
      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Filter by NFT Address:</label>
        <input
          type="text"
          id="nftAddressFilter"
          className="w-full p-2 border rounded-md shadow-sm"
          placeholder="Enter NFT address"
          value=""
          onChange={(e) => onFilterChange(e.target.value)}
          aria-label="Filter withdrawals by NFT address"
        />
      </div>

      {/* Withdrawal List */}
      <table className="table">
        <thead>
          <tr>
            <th>NFT Address</th>
            <th>Withdrawal ID</th>
            <th>Status</th>
            <th>Timestamp</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {filteredWithdrawals.map((withdrawal) => (
            <tr key={withdrawal.withdrawalId} aria-label={`Withdrawal ${withdrawal.withdrawalId}`}>
              <td>{withdrawal.nftAddress}</td>
              <td>{withdrawal.withdrawalId}</td>
              <td>{withdrawal.status}</td>
              <td>{withdrawal.timestamp}</td>
              <td>{withdrawal.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Real-time Data Visualization */}
      <div className="mt-4">
        <canvas
          id="withdrawalChart"
          width="400"
          height="200"
          className="rounded"
        >
          <Chart data={chartData} options={chartOptions} />
        </canvas>
      </div>
    </div>
  );
};

export default WithdrawalDashboard;