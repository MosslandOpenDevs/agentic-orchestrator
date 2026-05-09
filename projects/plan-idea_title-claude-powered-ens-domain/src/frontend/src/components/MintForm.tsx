import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hookform';
import { useToast } from 'react-toastify';

interface MetadataInput {
  name?: string;
  description?: string;
  image?: string;
  attributes?: { [key: string]: string }[];
}

interface BrandAssetGeneration {
  brandColor?: string;
  logoUrl?: string;
}

interface MintFormProps {
  initialMetadata?: MetadataInput;
  brandAssetGeneration?: BrandAssetGeneration;
}

const MintForm: React.FC<MintFormProps> = ({ initialMetadata, brandAssetGeneration }) => {
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<MetadataInput>({ defaultValues: initialMetadata || {} });

  const toast = useToast();

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null | undefined>(null);

  const onSubmit = async (data: MetadataInput) => {
    setIsLoading(true);
    setError(null);

    try {
      // Simulate minting process - Replace with actual minting logic
      await new Promise((resolve) => setTimeout(resolve, 2000));

      toast.success('NFT minted successfully!', {
        position: 'top-right',
        autoClose: 5000,
        theme: 'solid',
      });
      reset();
    } catch (err: any) {
      setError(err.message || 'An error occurred during minting.');
      toast.error(err.message, {
        position: 'top-right',
        autoClose: 5000,
        theme: 'solid',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (error) {
      // Handle error state - could trigger a retry or other actions
    }
  }, [error]);

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md overflow-hidden">
      <h2 className="text-xl font-bold mb-4">Mint New NFT</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="max-w-md">
        {/* Metadata Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
          <input
            type="text"
            {...register('name')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="NFT Name"
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <input
            type="text"
            {...register('description')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="NFT Description"
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Image URL</label>
          <input
            type="text"
            {...register('image')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="NFT Image URL"
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Attributes</label>
          <input
            type="text"
            {...register('attributes')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="NFT Attributes"
          />
        </div>

        {/* Brand Asset Generation */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Brand Color</label>
          <input
            type="color"
            {...register('brandColor')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="Brand Color"
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
          <input
            type="text"
            {...register('logoUrl')}
            className="w-full px-3 py-2 border rounded-md shadow-sm focus:outline-yellow-500 focus:border-yellow-500"
            aria-label="Logo URL"
          />
        </div>

        <button
          type="submit"
          className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded-md shadow-md w-full"
          disabled={isLoading}
        >
          {isLoading ? 'Minting...' : 'Mint NFT'}
        </button>
      </form>
    </div>
  );
};

export default MintForm;