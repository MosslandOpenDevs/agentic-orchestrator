import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hookform';
import { useToast } from 'react-toastify';

interface MetadataInput {
  name: string;
  description: string;
  image: string;
}

interface DomainSelection {
  name: string;
  url: string;
}

interface MintFormProps {
  initialMetadata?: MetadataInput;
  domains?: DomainSelection[];
  onSubmit?: (data: any) => Promise<void>;
}

const MintForm: React.FC<MintFormProps> = ({
  initialMetadata = { name: '', description: '', image: '' },
  domains = [],
  onSubmit,
} ) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: {
      name: initialMetadata.name,
      description: initialMetadata.description,
      image: initialMetadata.image,
      domain: domains[0]?.url || '',
    },
    resolver: (data) => ({
      name: data.name,
      description: data.description,
      image: data.image,
      domain: data.domain,
    }),
  });

  const toast = useToast();

  const submitHandler = async (data: any) => {
    try {
      const response = await onSubmit(data);
      if (response) {
        toast('NFT minted successfully!', { type: 'success' });
        reset();
      }
    } catch (error: any) {
      console.error('Error minting NFT:', error);
      toast(error.message || 'Failed to mint NFT', { type: 'error' });
    }
  };

  useEffect(() => {
    reset();
  }, [reset]);

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded-lg shadow-md overflow-hidden">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">Mint Your Mossland NFT</h1>

      <form onSubmit={handleSubmit(submitHandler)} className="max-w-md mx-4">
        {/* Metadata Input */}
        <div className="mb-4">
          <label className="text-gray-600 font-medium mb-1">Name:</label>
          <input
            type="text"
            {...register('name')}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            aria-label="NFT Name"
          />
          {errors.name && <p className="text-red-500 italic">{errors.name.message}</p>}
        </div>
        <div className="mb-4">
          <label className="text-gray-600 font-medium mb-1">Description:</label>
          <input
            type="text"
            {...register('description')}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            aria-label="NFT Description"
          />
          {errors.description && <p className="text-red-500 italic">{errors.description.message}</p>}
        </div>
        <div className="mb-4">
          <label className="text-gray-600 font-medium mb-1">Image URL:</label>
          <input
            type="text"
            {...register('image')}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            aria-label="NFT Image URL"
          />
          {errors.image && <p className="text-red-500 italic">{errors.image.message}</p>}
        </div>

        {/* Domain Selection */}
        <div className="mb-4">
          <label className="text-gray-600 font-medium mb-1">Domain:</label>
          <select
            {...register('domain')}
            className="w-full px-3 py-2 border rounded-md focus:outline-gray-200 focus:ring-2 focus:ring-blue-500"
            aria-label="Select Domain"
          >
            <option value="">-- Select Domain --</option>
            {domains.map((domain) => (
              <option key={domain.name} value={domain.url}>
                {domain.name}
              </option>
            ))}
          </select>
          {errors.domain && <p className="text-red-500 italic">{errors.domain.message}</p>}
        </div>

        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
          disabled={false}
        >
          Mint NFT
        </button>
      </form>
    </div>
  );
};

export default MintForm;