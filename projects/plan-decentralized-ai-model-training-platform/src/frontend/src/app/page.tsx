import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeftOnCircleIcon, UserIcon, ShieldIcon } from '@heroicons/react/24/solid';
import { useSession } from 'next/next';

// Dummy data for demonstration
interface Model {
  id: string;
  name: string;
  description: string;
  price: number;
  owner: string;
  // Add more model properties as needed
}

const models: Model[] = [
  { id: '1', name: 'Image Classifier', description: 'Classifies images', price: 10, owner: 'Alice' },
  { id: '2', name: 'Text Generator', description: 'Generates text', price: 15, owner: 'Bob' },
  { id: '3', name: 'Sentiment Analyzer', description: 'Analyzes sentiment', price: 8, owner: 'Charlie' },
];

const GenesisAI = () => {
  const router = useRouter();
  const { data: session } = useSession();
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (router.query.id) {
      const model = models.find((m) => m.id === router.query.id);
      if (model) {
        setSelectedModel(model);
      }
    }
  }, [router.query.id]);

  const handleNavigateBack = () => {
    window.goBack();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-100">
        <p>Loading Genesis AI Dashboard...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-800 dark:text-white">
      <header className="bg-gray-100 dark:bg-gray-800 shadow-md">
        <div className="container mx-auto px-4 flex items-center justify-between">
          <button onClick={handleNavigateBack} className="text-gray-600 dark:text-white hover:text-gray-800 dark:hover:text-gray-400">
            <ArrowLeftOnCircleIcon className="h-6 w-6" />
          </button>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Genesis AI</h1>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        {/* Model List */}
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">Available Models</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {models.map((model) => (
              <div
                key={model.id}
                className="bg-white rounded-lg shadow-md hover:shadow-xl transition duration-300 ease-in-out p-4"
              >
                <img src={`/images/model-${model.id}.png`} alt={model.name} className="w-20 h-20 object-cover rounded-md mx-auto mb-2" />
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">{model.name}</h3>
                <p className="text-gray-600 dark:text-white">By: {model.owner}</p>
                <p className="text-gray-600 dark:text-white">${model.price}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Model Details */}
        {selectedModel && (
          <div className="mb-6">
            <h2 className="text-xl font-bold mb-4">Model Details</h2>
            <div className="p-4">
              <h3 className="text-xl font-semibold">{selectedModel.name}</h3>
              <p className="text-gray-600 dark:text-white">Description: {selectedModel.description}</p>
              <p className="text-gray-600 dark:text-white">Price: ${selectedModel.price}</p>
              <p className="text-gray-600 dark:text-white">Owner: {selectedModel.owner}</p>
            </div>
          </div>
        )}

        {/* User Dashboard */}
        {session && (
          <div className="bg-gray-100 rounded-lg shadow-md p-4">
            <h3 className="text-xl font-semibold mb-4">User Dashboard</h3>
            <div className="grid grid-cols-1 gap-4">
              {/* Widget 1: Deployed Models */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <h4 className="text-lg font-semibold mb-2">Deployed Models</h4>
                <p className="text-gray-600 dark:text-white">You have deployed 0 models.</p>
              </div>

              {/* Widget 2: User Information */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <h4 className="text-lg font-semibold mb-2">User Information</h4>
                <p className="text-gray-600 dark:text-white">Welcome, {session.user.name}!</p>
                <p className="text-gray-600 dark:text-white">Email: {session.user.email}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GenesisAI;