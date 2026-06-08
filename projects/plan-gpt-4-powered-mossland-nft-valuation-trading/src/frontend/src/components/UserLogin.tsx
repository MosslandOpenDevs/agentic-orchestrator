import React, { useState } from 'react';

interface UserLoginProps {
  onSubmit: (data: any) => Promise<void>;
  isLoading: boolean;
  error?: string;
}

const UserLogin: React.FC<UserLoginProps> = ({ onSubmit, isLoading, error }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const data = {
        address: window.ethereum.selectedAddress, // Get user's address
        username,
        password,
      };

      await onSubmit(data);
    } catch (err: any) {
      console.error('Login error:', err);
      error && setError(err.message);
    }
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-md mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Login</h2>

      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-medium mb-2">Username</label>
        <input
          type="text"
          id="username"
          className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-400"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          aria-label="Username"
          tabIndex={0}
        />
      </div>

      <div className="mb-4">
        <label className="block text-gray-700 text-sm font-medium mb-2">Password</label>
        <input
          type="password"
          id="password"
          className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-400"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label="Password"
          tabIndex={0}
        />
      </div>

      <button
        onClick={handleLogin}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full transition duration-300"
        disabled={isLoading}
      >
        {isLoading ? 'Loading...' : 'Login'}
      </button>

      {error && (
        <div className="mt-4 p-4 rounded-md bg-red-100 border-red-500 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};

export default UserLogin;