import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface Asset {
  id: string;
  name: string;
  symbol: string;
  currentQuantity: number;
  minQuantity: number;
  maxQuantity: number;
}

interface RebalancingWizardProps {
  assets: Asset[];
  onRebalance: (assets: Asset[]) => void;
}

const RebalancingWizard: React.FC<RebalancingWizardProps> = ({ assets, onRebalance }) => {
  const [selectedAssets, setSelectedAssets] = useState<Asset[]>([]);
  const [currentQuantities, setCurrentQuantities] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const toast = useToast();

  useEffect(() => {
    if (selectedAssets.length > 0) {
      setCurrentQuantities(selectedAssets.map(asset => asset.minQuantity));
    } else {
      setCurrentQuantities([]);
    }
  }, [selectedAssets]);

  const handleAssetSelection = (asset: Asset) => {
    setSelectedAssets(prev => [...prev, asset]);
    setCurrentQuantities(prev => [...prev, asset.minQuantity]);
  };

  const handleQuantityChange = (index: number, quantity: number) => {
    const newQuantities = [...currentQuantities];
    newQuantities[index] = quantity;
    setCurrentQuantities(newQuantities);

    if (selectedAssets.length > 0) {
      const updatedAssets = selectedAssets.map((asset, i) => ({
        ...asset,
        currentQuantity: quantity,
      }));
      setSelectedAssets(updatedAssets);
    }
  };

  const handleRebalance = () => {
    if (selectedAssets.length === 0) {
      toast('Please select at least one asset to rebalance.', { type: 'error' });
      return;
    }

    setLoading(true);
    try {
      onRebalance(selectedAssets);
      toast.success('Portfolio rebalanced successfully!', { duration: 3000 });
    } catch (e: any) {
      setError(e.message || 'An error occurred during rebalancing.');
      toast.error(e.message || 'An error occurred during rebalancing.', { duration: 3000 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-screen-md mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Rebalancing Wizard</h1>

      {error && <div className="mt-2 p-2 rounded-md shadow-md bg-red-100 bg-red-500 text-red-700">
        {error}
      </div>}

      {loading && <p className="text-center mt-4">Rebalancing...</p>}

      <div className="grid grid-cols-1 gap-4 mb-4">
        {assets.map(asset => (
          <div
            key={asset.id}
            className="bg-white rounded-md shadow-sm p-4 hover:bg-gray-100 flex items-center"
            aria-label={`Rebalance ${asset.symbol}`}
          >
            <input
              type="number"
              min={asset.minQuantity}
              max={asset.maxQuantity}
              value={currentQuantities[assets.indexOf(asset)]}
              onChange={(e) => handleQuantityChange(assets.indexOf(asset), parseInt(e.target.value, 10))}
              className="w-full h-full p-2 border rounded focus:outline-yellow-500 focus:border-yellow-500"
              tabIndex={0}
            />
            <p className="ml-2">{asset.name} ({asset.symbol})</p>
          </div>
        ))}
      </div>

      <button
        onClick={handleRebalance}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
        disabled={loading}
        aria-label="Rebalance Portfolio"
      >
        Rebalance
      </button>
    </div>
  );
};

export default RebalancingWizard;