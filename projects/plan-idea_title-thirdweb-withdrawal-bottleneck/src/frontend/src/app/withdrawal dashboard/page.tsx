import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface WithdrawalData {
  transactionId: string;
  status: 'pending' | 'success' | 'failed' | 'cancelled';
  timestamp: string;
  amount: number;
  nftAddress?: string;
}

interface WithdrawalDashboardProps {
  initialData?: WithdrawalData[];
}

const WithdrawalDashboard: React.FC<WithdrawalDashboardProps> = ({ initialData = [] }) => {
  const [withdrawals, setWithdrawals] = useState<WithdrawalData[]>(initialData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const filterStatus = searchParams.get('status') || 'all';

  useEffect(() => {
    setLoading(true);
    setError(null);

    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const data: WithdrawalData[] = [
          { transactionId: 'TX123', status: 'pending', timestamp: '2024-01-01T10:00:00Z', amount: 1.5 },
          { transactionId: 'TX456', status: 'success', timestamp: '2024-01-01T10:15:00Z', amount: 2.0, nftAddress: '0x...' },
          { transactionId: 'TX789', status: 'failed', timestamp: '2024-01-01T10:30:00Z', amount: 1.0 },
          { transactionId: 'TX101', status: 'pending', timestamp: '2024-01-01T10:45:00Z', amount: 0.75 },
          { transactionId: 'TX112', status: 'cancelled', timestamp: '2024-01-01T11:00:00Z', amount: 1.2 },
        ];

        setWithdrawals(data);
      } catch (err) {
        setError('Failed to fetch withdrawal data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div>Loading withdrawal data...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">NFT Withdrawal Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {withdrawals.map((withdrawal) => (
          <div
            key={withdrawal.transactionId}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300"
            aria-label={`Withdrawal status for ${withdrawal.transactionId}`}
          >
            <p className="text-gray-700 mb-2">Transaction ID: {withdrawal.transactionId}</p>
            <p className="text-xl font-semibold mb-2">Status: {withdrawal.status}</p>
            <p className="text-gray-700 mb-2">Timestamp: {withdrawal.timestamp}</p>
            <p className="text-gray-700 mb-2">Amount: {withdrawal.amount} </p>
            {withdrawal.nftAddress && <p className="text-gray-700 mb-2">NFT Address: {withdrawal.nftAddress}</p>}
          </div>
        ))}
      </div>

      {/* Filter Component - Placeholder */}
      <div className="mt-4">
        <label className="text-gray-700 mb-1">Filter by Status:</label>
        <select
          className="bg-gray-100 border border-gray-300 rounded-md py-2 px-4"
          onChange={(e) => setSearchParams('status', e.target.value)}
        >
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
    </div>
  );
};

export default WithdrawalDashboard;