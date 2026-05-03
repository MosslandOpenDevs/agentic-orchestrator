import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface Model {
  id: string;
  name: string;
  description: string;
  provider: string;
  price: number;
  capabilities: string[];
  // Add other relevant model properties here
}

interface ModelListProps {
  models: Model[];
  isLoading: boolean;
  hasError: boolean;
  onFilterChange: (filter: string) => void;
  onSortChange: (sortField: string, sortOrder: 'asc' | 'desc') => void;
}

const ModelList: React.FC<ModelListProps> = ({
  models,
  isLoading,
  hasError,
  onFilterChange,
  onSortChange,
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filter = searchParams.get('filter') || '';
  const sortField = searchParams.get('sortField') || 'name';
  const sortOrder = searchParams.get('sortOrder') || 'asc';

  useEffect(() => {
    onFilterChange(filter);
  }, [filter, onFilterChange]);

  useEffect(() => {
    onSortChange(sortField, sortOrder);
  }, [sortField, sortOrder, onSortChange]);

  if (isLoading) {
    return <div>Loading models...</div>;
  }

  if (hasError) {
    return <div>Error loading models.</div>;
  }

  const sortedModels = [...models].sort((a, b) => {
    const order = sortOrder === 'desc' ? -1 : 1;
    return a[sortField].toLowerCase() > b[sortField].toLowerCase() ? 1 * order : -1 * order;
  });

  const filteredModels = sortedModels.filter(model =>
    model.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="max-w-screen-md mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">AI Model List</h1>

      {/* Filter */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by name..."
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          aria-label="Filter models by name"
          className="px-3 py-2 border rounded w-full max-w-sm"
        />
      </div>

      {/* Sort */}
      <div className="mb-4">
        <label className="text-base font-semibold mr-2">Sort by:</label>
        <select
          value={sortField}
          onChange={(e) => onSortChange(e.target.value, 'asc')}
          aria-label="Sort models by name"
          className="px-3 py-2 border rounded w-full max-w-sm"
        >
          <option value="name" >Name</option>
          <option value="provider" >Provider</option>
          <option value="price" >Price</option>
        </select>
        <span className="text-sm">Asc | Desc</span>
      </div>

      {/* Model List */}
      <ul
        className="list-group-horizontal"
        role="list"
        aria-label="List of AI Models"
      >
        {filteredModels.map((model) => (
          <li
            key={model.id}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-xl transition duration-300 ease-in-out"
            role="listitem"
            tabIndex={0}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                alert(`Details for ${model.name}`); // Replace with actual detail view
              }
            }}
          >
            <h3 className="text-lg font-semibold mb-2">{model.name}</h3>
            <p className="text-gray-700"><strong>Provider:</strong> {model.provider}</p>
            <p className="text-gray-700"><strong>Price:</strong> ${model.price}</p>
            <p className="text-gray-700"><strong>Description:</strong> {model.description}</p>
            <p className="text-gray-700"><strong>Capabilities:</strong> {model.capabilities.join(', ')}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ModelList;