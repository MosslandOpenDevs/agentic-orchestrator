import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../hooks/auth'; // Assuming auth hook is in hooks/auth.ts
import { NFTData } from '../../types/NFTData';
import { RiskAlert } from '../../types/RiskAlert';

// Dummy data for demonstration - Replace with actual API calls
const mockNFTData: NFTData[] = [
  { id: 'nft1', name: 'Mossland Token', value: 100 },
  { id: 'nft2', name: 'Terra Token', value: 50 },
];

const mockRiskAlerts: RiskAlert[] = [
  { id: 'alert1', message: 'Potential market volatility detected', severity: 'high' },
  { id: 'alert2', message: 'Terra price decreasing', severity: 'medium' },
];

const MainPage = () => {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
    setLoading(false);
  }, [user, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-red-100">
        <p>Error: {error}</p>
        <button onClick={() => router.push('/')} className="bg-green-500 text-white px-4 py-2 rounded-md">
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      {user ? (
        <>
          <h1 className="text-2xl font-bold mb-4">Mossland Dashboard</h1>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-md shadow-md p-4">
              <h3 className="text-lg font-semibold mb-2">Portfolio Overview</h3>
              <p className="text-gray-700">
                Total Portfolio Value: ${mockNFTData.reduce((acc, nft) => acc + nft.value, 0)}
              </p>
              {mockNFTData.map((nft) => (
                <div key={nft.id} className="flex items-center mb-2">
                  <span className="text-xl">{nft.name}</span>
                  <span className="text-gray-600 ml-2">{nft.value}</span>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-md shadow-md p-4">
              <h3 className="text-lg font-semibold mb-2">NFT Valuation</h3>
              <p className="text-gray-700">
                This section will provide NFT valuation insights.
              </p>
            </div>

            <div className="bg-white rounded-md shadow-md p-4">
              <h3 className="text-lg font-semibold mb-2">Risk Alerts</h3>
              {mockRiskAlerts.map((alert) => (
                <div key={alert.id} className="flex items-center mb-2">
                  <span className="text-lg font-semibold">{alert.message}</span>
                  <span className="text-gray-600 ml-2">{alert.severity}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <button
              className="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-700"
              onClick={logout}
              aria-label="Logout"
            >
              Logout
            </button>
          </div>
        </>
      ) : (
        <div className="bg-gray-100 p-4 rounded-md">
          <p>Please log in to access your Mossland dashboard.</p>
          <button onClick={() => router.push('/login')} className="bg-blue-500 text-white px-4 py-2 rounded-md">
            Login
          </button>
        </div>
      )}
    </div>
  );
};

export default MainPage;