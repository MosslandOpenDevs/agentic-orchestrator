import React, { useState } from 'react';

interface UserRegistrationProps {
  onSubmit: (data: UserData) => void;
  isLoading?: boolean;
  error?: string;
}

interface UserData {
  address: string;
  password: string;
}

const UserRegistration: React.FC<UserRegistrationProps> = ({ onSubmit, isLoading = false, error }) => {
  const [address, setAddress] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!address || !password) {
      setErrorMessage('Please fill in all fields.');
      return;
    }

    const data: UserData = {
      address,
      password,
    };

    onSubmit(data);
  };

  return (
    <div className="max-w-md mx-auto py-8 px-4 rounded-lg shadow-md overflow-hidden">
      <h2 className="text-2xl font-semibold text-center mb-6">Register</h2>

      {error && <p className="text-red-500 text-center mb-4">{error}</p>}

      <form onSubmit={handleSubmit} className="max-w-md mx-4 py-4 px-6">
        <div className="mb-4">
          <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">Address</label>
          <input
            type="text"
            id="address"
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            aria-label="Enter your address"
            tabIndex={0}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">Password</label>
          <input
            type="password"
            id="password"
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:border-blue-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            aria-label="Enter your password"
            tabIndex={0}
          />
        </div>

        <button
          type="submit"
          className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white font-medium rounded-md shadow-md disabled:opacity-50"
          disabled={isLoading}
        >
          {isLoading ? 'Submitting...' : 'Register'}
        </button>
      </form>
    </div>
  );
};

export default UserRegistration;