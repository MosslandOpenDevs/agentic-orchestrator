import React, { useState, useEffect } from 'react';

interface NFTGeneratorFormProps {
  onGenerate: (prompt: string) => void;
}

const NFTGeneratorForm: React.FC<NFTGeneratorFormProps> = ({ onGenerate }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(e.target.value);
  };

  const handleGenerate = async () => {
    if (!prompt) {
      setError('Prompt cannot be empty.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Simulate NFT generation with a delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      onGenerate(prompt);
    } catch (err) {
      setError('Failed to generate NFT. Please try again.');
      console.error('Error generating NFT:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md bg-white">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">NFT Generator</h2>

      <div className="mb-4">
        <label className="block text-gray-700 font-semibold mb-2">Prompt:</label>
        <input
          type="text"
          id="prompt"
          className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:border-blue-500"
          value={prompt}
          onChange={handleInputChange}
          aria-label="Enter NFT prompt"
          tabIndex={0}
        />
      </div>

      <button
        onClick={handleGenerate}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
        disabled={loading}
        aria-label="Generate NFT"
        tabIndex={0}
      >
        {loading ? 'Generating...' : 'Generate NFT'}
      </button>

      {error && (
        <div className="mt-4 p-4 rounded-md shadow-md bg-red-100 border-red-500 text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};

export default NFTGeneratorForm;