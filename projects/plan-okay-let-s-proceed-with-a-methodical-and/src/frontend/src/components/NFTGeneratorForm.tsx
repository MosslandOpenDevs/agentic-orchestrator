import React, { useState, useEffect } from 'react';

interface NFTGeneratorFormProps {
  onGenerate: (prompt: string) => void;
}

const NFTGeneratorForm: React.FC<NFTGeneratorFormProps> = ({ onGenerate }) => {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(e.target.value);
  };

  const handleGenerate = async () => {
    if (!prompt) {
      setError('Prompt cannot be empty.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await onGenerate(prompt);
    } catch (err: any) {
      setError(err.message || 'An error occurred during generation.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md bg-white">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">NFT Generator</h2>

      <div className="mb-4">
        <label htmlFor="promptInput" className="sr-only">Prompt:</label>
        <input
          type="text"
          id="promptInput"
          className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
          value={prompt}
          onChange={handleInputChange}
          aria-label="Enter prompt for NFT generation"
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleGenerate();
            }
          }}
        />
      </div>

      <button
        onClick={handleGenerate}
        className="w-full px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white font-bold rounded-md shadow-md disabled:opacity-50"
        disabled={isLoading}
        aria-label="Generate NFT"
      >
        {isLoading ? 'Generating...' : 'Generate NFT'}
      </button>

      {error && (
        <div className="mt-4 p-4 rounded-md bg-red-100 border-red-500 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};

export default NFTGeneratorForm;