import React, { useState, useEffect } from 'react';
import { useSession } from 'next-session';
import { useRouter } from 'next/router';

interface Model {
  id: string;
  name: string;
  status: 'deployed' | 'pending' | 'failed';
  // Add more model properties as needed
}

interface UserDashboardProps {
  initialModels?: Model[];
}

const UserDashboard: React.FC<UserDashboardProps> = ({ initialModels = [] }) => {
  const { data: sessionData } = useSession();
  const router = useRouter();
  const [models, setModels] = useState<Model[]>(initialModels);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionData) {
      router.push('/login');
      return;
    }

    // Simulate fetching models from an API
    const fetchModels = async () => {
      try {
        const response = await fetch(`/api/models?userId=${sessionData.userId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data: Model[] = await response.json();
        setModels(data);
        setLoading(false);
      } catch (error) {
        setError(error as string);
        setLoading(false);
      }
    };

    fetchModels();
  }, [sessionData]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">User Dashboard</h1>
        <p className="text-gray-600">Loading models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">User Dashboard</h1>
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">User Dashboard</h1>

      {/* Model List */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Deployed Models</h2>
        <ul className="list-disc space-y-2">
          {models
            .filter((model) => model.status === 'deployed')
            .map((model) => (
              <li
                key={model.id}
                className="flex items-center space-x-2"
                aria-label={`Model: ${model.name}`}
              >
                {model.name}
              </li>
            ))}
        </ul>
      </div>

      {/* Transaction History (Placeholder) */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Transaction History</h2>
        <p className="text-gray-600">Transaction data will be displayed here.</p>
      </div>
    </div>
  );
};

export default UserDashboard;