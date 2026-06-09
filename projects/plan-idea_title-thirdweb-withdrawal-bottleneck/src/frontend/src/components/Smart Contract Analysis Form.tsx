import React, { useState, useEffect } from 'react';

interface SmartContractAnalysisFormProps {
  onSubmit: (data: { smartContractData: string; query: string }) => void;
}

const SmartContractAnalysisForm: React.FC<SmartContractAnalysisFormProps> = ({ onSubmit }) => {
  const [smartContractData, setSmartContractData] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSmartContractDataChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSmartContractData(e.target.value);
  };

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const data = { smartContractData, query };
      onSubmit(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      console.error('Error submitting form:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // No specific effect needed for this component's functionality
  }, []);

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md overflow-hidden">
      <form onSubmit={handleSubmit} aria-label="Smart Contract Analysis Form">
        <h2 className="text-xl font-semibold mb-4">Smart Contract Analysis</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="smartContractData">
            Smart Contract Data:
            <span aria-hidden="true" className="ml-1 text-gray-500">
              (e.g., ABI, Source Code)
            </span>
          </label>
          <input
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            type="text"
            id="smartContractData"
            value={smartContractData}
            onChange={handleSmartContractDataChange}
            placeholder="Enter Smart Contract Data"
            aria-label="Enter Smart Contract Data"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="query">
            Query:
            <span aria-hidden="true" className="ml-1 text-gray-500">
              (e.g., "Analyze this contract")
            </span>
          </label>
          <input
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            type="text"
            id="query"
            value={query}
            onChange={handleQueryChange}
            placeholder="Enter Query"
            aria-label="Enter Query"
          />
        </div>

        <button
          className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white font-bold rounded-md shadow-md"
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>

        {error && (
          <div className="mt-4 p-4 rounded-b bg-red-100 border-l-4 border-red-500">
            <p className="text-sm font-semibold text-red-700">
              Error: {error}
            </p>
          </div>
        )}
      </form>
    </div>
  );
};

export default SmartContractAnalysisForm;