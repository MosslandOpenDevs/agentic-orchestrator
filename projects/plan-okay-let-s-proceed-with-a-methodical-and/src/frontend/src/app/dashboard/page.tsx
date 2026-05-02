import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useSession } from 'next-auth/react';

// Define interfaces
interface UserProfileData {
  username: string;
  // Add other user data fields here
}

interface DashboardProps {
  initialData?: any; // Allow passing initial data from an API
}

const Dashboard: React.FC<DashboardProps> = ({ initialData }) => {
  const { data: session } = useSession();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userData, setUserData] = useState<UserProfileData | null>(null);

  useEffect(() => {
    if (!session) {
      router.push('/login');
      return;
    }

    // Simulate fetching user data (replace with actual API call)
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/user/${session.user.id}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch user data: ${response.status}`);
        }
        const data = await response.json();
        setUserData(data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [session?.user?.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (!session) {
    return null; // Or redirect to login page
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-2xl font-bold mb-4">Welcome, {session.user.username}!</h1>

      {/* NFT Generation Button */}
      <button
        onClick={() => router.push('/nft-generation')}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
        aria-label="Generate NFT"
      >
        Generate NFT
      </button>

      {/* User Profile */}
      <div className="mt-4">
        <p className="font-semibold mb-2">User Profile:</p>
        {userData && (
          <div className="space-y-4">
            <p className="text-gray-700">Username: {userData.username}</p>
            {/* Add more user data fields here */}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;