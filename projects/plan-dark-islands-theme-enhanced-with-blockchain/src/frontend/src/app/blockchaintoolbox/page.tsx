import React, { useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';

interface BlockchainToolboxProps {
  network: string;
}

const BlockchainToolbox: React.FC<BlockchainToolboxProps> = ({ network }) => {
  const [contractCode, setContractCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleCompile = async () => {
    try {
      setLoading(true);
      setError(null);

      // Placeholder for actual contract compilation logic
      const response = await axios.post('/api/compile', { code: contractCode });
      console.log('Compilation successful:', response.data);
    } catch (err) {
      setError(err.message || 'An error occurred during compilation.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async () => {
    try {
      setLoading(true);
      setError(null);

      // Placeholder for actual deployment logic
      const response = await axios.post('/api/deploy', { code: contractCode, network });
      console.log('Deployment successful:', response.data);
    } catch (err) {
      setError(err.message || 'An error occurred during deployment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <textarea
        aria-label="Contract Code Input"
        value={contractCode}
        onChange={(e) => setContractCode(e.target.value)}
        placeholder="Enter your contract code here..."
        className="w-full max-w-md p-4 mb-4 rounded-lg shadow-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div className="flex space-x-2">
        <button
          onClick={handleCompile}
          disabled={loading || !contractCode.trim()}
          aria-label="Compile Contract Button"
          className={`px-4 py-2 text-white rounded-lg shadow-md bg-blue-500 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Compile
        </button>
        <button
          onClick={handleDeploy}
          disabled={loading || !contractCode.trim()}
          aria-label="Deploy Contract Button"
          className={`px-4 py-2 text-white rounded-lg shadow-md bg-green-500 hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          Deploy to {network}
        </button>
      </div>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {loading && <p className="mt-4">Loading...</p>}
    </div>
  );
};

export default BlockchainToolbox;