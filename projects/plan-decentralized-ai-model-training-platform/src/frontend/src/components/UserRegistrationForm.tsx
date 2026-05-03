import React, { useState } from 'react';

interface AddressInputProps {
  onSubmit: (data: FormData) => void;
}

const UserRegistrationForm: React.FC<AddressInputProps> = ({ onSubmit }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState<string>('');
  const [lastName, setLastName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [city, setCity] = useState<string>('');
  const [state, setState] = useState<string>('');
  const [zip, setZip] = useState<string>('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setError(null);

    if (!firstName || !lastName || !email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    const data = new FormData({
      firstName,
      lastName,
      email,
      password,
      address,
      city,
      state,
      zip,
    });

    setLoading(true);
    onSubmit(data);
  };

  return (
    <div className="max-w-md mx-auto py-8 px-4 rounded-lg shadow-md overflow-hidden bg-white">
      <form onSubmit={handleSubmit} aria-label="User Registration Form">
        <h2 className="text-2xl font-bold text-center mb-6">Register</h2>

        <div className="mb-4">
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
          <input
            type="text"
            id="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="First Name"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
          <input
            type="text"
            id="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="Last Name"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="Email"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="Password"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">Address</label>
          <input
            type="text"
            id="address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="Address"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">City</label>
          <input
            type="text"
            id="city"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="City"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">State</label>
          <input
            type="text"
            id="state"
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="State"
            autoFocus
          />
        </div>

        <div className="mb-4">
          <label htmlFor="zip" className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
          <input
            type="text"
            id="zip"
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-gray-300 text-gray-700"
            aria-label="Zip Code"
            autoFocus
          />
        </div>

        {error && <p className="text-red-500 text-center mb-4">{error}</p>}

        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full max-w-md"
          disabled={loading}
          aria-label="Register"
        >
          {loading ? 'Submitting...' : 'Register'}
        </button>
      </form>
    </div>
  );
};

export default UserRegistrationForm;