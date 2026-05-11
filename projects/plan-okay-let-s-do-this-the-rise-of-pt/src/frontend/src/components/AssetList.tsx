import React, { useState, useEffect } from 'react';

interface Asset {
  id: string;
  name: string;
  quantity: number;
  value: number;
}

interface AssetListProps {
  assets: Asset[];
  isLoading: boolean;
  error?: string;
}

const AssetList: React.FC<AssetListProps> = ({ assets, isLoading, error }) => {
  if (isLoading) {
    return <div>Loading assets...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!assets || assets.length === 0) {
    return <div>No assets found.</div>;
  }

  return (
    <ul className="list-group">
      {assets.map((asset) => (
        <li key={asset.id} className="list-group-item">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <strong>{asset.name}</strong><br />
              Quantity: {asset.quantity}<br />
              Value: ${asset.value}
            </div>
            {/* Accessibility - aria-label for keyboard navigation */}
            <span aria-label={`Asset details for ${asset.name}`} className="ms-auto">
              {/* Add keyboard navigation logic here if needed */}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
};

export default AssetList;