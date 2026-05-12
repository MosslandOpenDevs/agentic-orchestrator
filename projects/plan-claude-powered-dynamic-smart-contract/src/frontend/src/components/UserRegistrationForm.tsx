import React, { useState } from 'react';

interface UserRegistrationFormProps {
  onSubmit: (userData: UserData) => void;
  isLoading: boolean;
  error?: string;
}

interface UserData {
  username: string;
  email: string;
  role: string;
}

const UserRegistrationForm: React.FC<UserRegistrationFormProps> = ({
  onSubmit,
  isLoading,
  error,
}) => {
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [role, setRole] = useState<string>('');
  const [isError, setIsError] = useState<boolean>(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !email || !role) {
      setIsError(true);
      return;
    }

    const userData: UserData = {
      username,
      email,
      role,
    };

    onSubmit(userData);
    setIsError(false);
  };

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md bg-white">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">
        Register
      </h1>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="mb-2">
          <label
            htmlFor="username"
            className="text-gray-600 text-sm font-medium mb-1"
            aria-label="Username"
          >
            Username
          </label>
          <input
            type="text"
            id="username"
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
          />
        </div>

        <div className="mb-2">
          <label
            htmlFor="email"
            className="text-gray-600 text-sm font-medium mb-1"
            aria-label="Email"
          >
            Email
          </label>
          <input
            type="email"
            id="email"
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="mb-2">
          <label
            htmlFor="role"
            className="text-gray-600 text-sm font-medium mb-1"
            aria-label="Role"
          >
            Role
          </label>
          <input
            type="text"
            id="role"
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
        </div>

        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white w-full px-4 py-2 rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          {isLoading ? 'Submitting...' : 'Register'}
        </button>
      </form>
    </div>
  );
};

export default UserRegistrationForm;