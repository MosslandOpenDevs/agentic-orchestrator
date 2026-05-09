import React, { useState, useEffect } from 'react';
import { useSession } from 'next-session';
import { useRouter } from 'next/router';

interface ENSDomain {
  name: string;
  tokenId: string;
  price: number;
  createdAt: string;
  updatedAt: string;
}

interface DomainDashboardProps {
  initialDomains?: ENSDomain[];
}

const DomainDashboard: React.FC<DomainDashboardProps> = ({ initialDomains = [] }) => {
  const { data: session } = useSession();
  const router = useRouter();
  const [domains, setDomains] = useState<ENSDomain[]>(initialDomains);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) {
      router.push('/login');
      return;
    }

    // Simulate fetching domains from an API. Replace with your actual API call.
    const fetchDomains = async () => {
      try {
        const response = await fetch('https://api.mossland.com/domains', {
          headers: {
            'Authorization': session.token,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data: ENSDomain[] = await response.json();
        setDomains(data);
        setLoading(false);
      } catch (error: any) {
        setError(error.message);
        setLoading(false);
      }
    };

    fetchDomains();
  }, [session]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Domain Dashboard</h1>
        <p className="text-gray-600">Loading domains...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Domain Dashboard</h1>
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Domain Dashboard</h1>
      <table className="min-w-table mx-auto">
        <thead>
          <tr className="text-left">
            <th className="px-4 py-2 border-b">Domain Name</th>
            <th className="px-4 py-2 border-b">Token ID</th>
            <th className="px-4 py-2 border-b">Price</th>
            <th className="px-4 py-2 border-b">Created At</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {domains.map((domain) => (
            <tr key={domain.tokenId} className="text-left cursor-pointer" aria-label={`View details for ${domain.name}`}>
              <td className="px-4 py-2">{domain.name}</td>
              <td className="px-4 py-2">{domain.tokenId}</td>
              <td className="px-4 py-2">${domain.price.toFixed(2)}</td>
              <td className="px-4 py-2">{domain.createdAt}</td>
              <td className="px-4 py-2">
                <button
                  onClick={() => router.push(`/domains/${domain.tokenId}`)}
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                  aria-label={`View details for ${domain.name}`}
                >
                  View Details
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DomainDashboard;