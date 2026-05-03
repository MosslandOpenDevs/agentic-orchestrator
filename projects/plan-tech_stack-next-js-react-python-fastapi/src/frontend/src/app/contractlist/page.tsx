import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeftIcon, ArrowRightIcon } from '@heroicons/react/24/solid';
import {
  ChartBarFixedRatio,
  ChartLine,
  ChartPieFixed,
  ChartStacked1D,
} from 'Chart.js';

interface Contract {
  id: string;
  name: string;
  type: 'erc20' | 'erc721' | 'other';
  description?: string;
  // Add other relevant contract properties here
}

interface ContractListProps {
  contracts: Contract[];
}

const ContractList: React.FC<ContractListProps> = ({ contracts }) => {
  const [filteredContracts, setFilteredContracts] = useState<Contract[]>(contracts);
  const [sortOrder, setSortOrder] = useState<string>('asc');
  const [sortBy, setSortBy] = useState<string>('name');
  const router = useRouter();

  useEffect(() => {
    setFilteredContracts(contracts);
  }, [contracts]);

  const handleSort = (criteria: string) => {
    if (sortBy === criteria) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortOrder('asc');
      setSortBy(criteria);
    }
  };

  const sortedContracts = [...contracts].sort((a, b) => {
    const order = sortOrder === 'desc' ? 'reverse' : '';
    if (criteria === 'name') {
      return a.name.localeCompare(b.name, order);
    }
    // Add other sorting criteria here
    return 0;
  });

  const handleViewContract = (id: string) => {
    router.push(`/contract/${id}`);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Contract List</h1>

      {/* Filters */}
      <div className="mb-4 flex items-center space-x-3">
        <button
          onClick={() => handleSort('name')}
          className={`px-3 py-2 rounded-md ${sortBy === 'name' ? 'bg-gray-200' : ''}`}
        >
          Sort by Name
        </button>
        <button
          onClick={() => handleSort('type')}
          className={`px-3 py-2 rounded-md ${sortBy === 'type' ? 'bg-gray-200' : ''}`}
        >
          Sort by Type
        </button>
      </div>

      {/* Contract List */}
      <ul className="space-y-4">
        {filteredContracts.map((contract) => (
          <li
            key={contract.id}
            className="bg-white rounded-md shadow-md p-4 hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`Contract: ${contract.name}`}
          >
            <div className="flex items-center space-x-3">
              <div>
                <span className="text-xl font-medium">{contract.name}</span>
                <span className="text-gray-600">{contract.type}</span>
                {contract.description && <p className="text-gray-700">{contract.description}</p>}
              </div>
              <button
                onClick={() => handleViewContract(contract.id)}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
              >
                View
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContractList;