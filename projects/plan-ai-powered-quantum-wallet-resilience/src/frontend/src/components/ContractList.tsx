import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface Contract {
  name: string;
  riskScore: number;
  summary: string;
}

interface ContractListProps {
  contracts: Contract[];
}

const ContractList: React.FC<ContractListProps> = ({ contracts }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchString = searchParams.get('search');
  const [filterRiskScore, setFilterRiskScore] = useState<number | null>(null);

  useEffect(() => {
    if (searchString) {
      setSearchParams({ search: searchString });
    } else {
      setSearchParams({});
    }
  }, [searchString]);

  const filteredContracts = contracts.filter((contract) => {
    if (!searchString) {
      return true;
    }
    return (
      contract.name.toLowerCase().includes(searchString.toLowerCase())
    );
  });

  const riskScoreFilteredContracts = filterRiskScore
    ? filteredContracts.filter((contract) => contract.riskScore <= filterRiskScore)
    : filteredContracts;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Contract List</h1>

      {/* Search Input */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name..."
          className="px-3 py-2 border rounded-md focus:outline-blue-200 focus:ring-2 focus:ring-blue-500"
          onChange={(e) => {
            setSearchParams({ search: e.target.value });
          }}
        />
      </div>

      {/* Risk Score Filter */}
      <div className="mb-4">
        <label className="text-base font-semibold mr-2">Filter by Risk Score:</label>
        <select
          className="px-3 py-2 border rounded-md focus:outline-blue-200 focus:ring-2 focus:ring-blue-500"
          onChange={(e) => setFilterRiskScore(parseInt(e.target.value))}
          value={filterRiskScore !== null ? filterRiskScore : ''}
        >
          <option value="" disabled>
            All Risk Scores
          </option>
          <option value="1">Low (1)</option>
          <option value="2">Medium (2)</option>
          <option value="3">High (3)</option>
        </select>
      </div>

      {/* Contract List */}
      <ul
        className="list-group"
        aria-label="Contract List"
      >
        {riskScoreFilteredContracts.map((contract) => (
          <li
            key={contract.name}
            className="bg-white shadow-md rounded-md p-4 hover:shadow-lg transition-shadow duration-300"
            role="listitem"
            aria-label={`Contract: ${contract.name}`}
          >
            <h3 className="text-xl font-semibold mb-2">{contract.name}</h3>
            <p className="text-gray-700">Risk Score: {contract.riskScore}</p>
            <p className="text-gray-700">{contract.summary}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContractList;