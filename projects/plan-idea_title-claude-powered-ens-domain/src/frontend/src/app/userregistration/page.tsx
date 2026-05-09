import React, { useState } from 'react';

interface UserRegistrationProps {
  onSubmit: (userData: UserData) => void;
}

interface UserData {
  username: string;
  password?: string;
  address?: string;
}

const UserRegistration: React.FC<UserRegistrationProps> = ({ onSubmit }) => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username) {
      setError('Username is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await onSubmit({ username, password, address });
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-center mb-4">Register</h1>

      <form onSubmit={handleSubmit} className="mt-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
          <input
            type="text"
            id="username"
            placeholder="Enter username"
            className="w-full px-4 py-3 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            aria-label="Username"
            tabIndex={0}
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
          <input
            type="password"
            id="password"
            placeholder="Enter password"
            className="w-full px-4 py-3 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-label="Password"
            tabIndex={0}
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
          <input
            type="text"
            id="address"
            placeholder="Enter address"
            className="w-full px-4 py-3 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            aria-label="Address"
            tabIndex={0}
          />
        </div>

        <button
          type="submit"
          className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-3 px-6 rounded-md shadow-md w-full max-w-md mx-auto"
          disabled={isLoading}
        >
          {isLoading ? 'Registering...' : 'Register'}
        </button>

        {error && (
          <div className="mt-4 p-4 rounded-md mb-4 bg-red-100 border-l-4 border-red-600 text-red-700">
            {error}
          </div>
        )}
      </form>
    </div>
  );
};

export default UserRegistration;