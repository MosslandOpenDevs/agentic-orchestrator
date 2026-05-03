import React, { useState, useEffect } from 'react';

interface ModelDetailsProps {
  modelId: string;
  modelData: {
    description: string;
    nvidiaNGCDetails?: {
      gpuRequirements: string;
      containerImage: string;
      version: string;
    };
    deploymentOptions?: string[];
  };
}

const ModelDetails: React.FC<ModelDetailsProps> = ({ modelId, modelData }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!modelId || !modelData) {
      setError('Invalid model data or ID.');
      setLoading(false);
      return;
    }

    setLoading(true);
    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, [modelId, modelData]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Loading model details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-8 rounded-lg shadow-md flex items-center justify-center">
        <p className="text-gray-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-lg shadow-md flex">
      <div className="md:w-6/12">
        <h2 className="text-2xl font-bold mb-4">
          {modelData.description}
        </h2>

        {modelData.nvidiaNGCDetails && (
          <div className="mb-4">
            <p className="text-gray-700 font-semibold">Nvidia NGC Details:</p>
            <p className="text-gray-600">
              GPU Requirements: {modelData.nvidiaNGCDetails.gpuRequirements}
            </p>
            <p className="text-gray-600">
              Container Image: {modelData.nvidiaNGCDetails.containerImage}
            </p>
            <p className="text-gray-600">
              Version: {modelData.nvidiaNGCDetails.version}
            </p>
          </div>
        )}

        {modelData.deploymentOptions && (
          <div className="mb-4">
            <p className="text-gray-700 font-semibold">Deployment Options:</p>
            <ul className="list-disc text-gray-600">
              {modelData.deploymentOptions.map((option) => (
                <li key={option} className="text-gray-600">
                  {option}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="md:w-6/12">
        <img
          src="https://via.placeholder.com/400x300"
          alt={`Model ${modelId} Image`}
          aria-label={`Model ${modelId} Image`}
          className="w-full h-full object-cover rounded-md"
        />
      </div>
    </div>
  );
};

export default ModelDetails;