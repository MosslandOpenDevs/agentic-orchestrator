import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface ENSDomain {
  name: string;
  price: number;
  available: boolean;
}

interface DomainListProps {
  domains?: ENSDomain[];
  loading?: boolean;
  error?: string;
}

const DomainList: React.FC<DomainListProps> = ({ domains = [], loading = false, error }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filterText = searchParams.get('filter') || '';
  const sortField = searchParams.get('sort') || 'price';
  const sortOrder = searchParams.get('order') || 'asc';

  const [filteredDomains, setFilteredDomains] = useState<ENSDomain[]>(domains);
  const [sortedDomains, setSortedDomains] = useState<ENSDomain[]>(domains);

  useEffect(() => {
    if (filterText) {
      const filtered = domains.filter(domain =>
        domain.name.toLowerCase().includes(filterText.toLowerCase())
      );
      setFilteredDomains(filtered);
    } else {
      setFilteredDomains(domains);
    }
  }, [domains, filterText]);

  useEffect(() => {
    if (sortField === 'name') {
      const sorted = [...sortedDomains].sort((a, b) => a.name.localeCompare(b.name));
      setSortedDomains(sorted);
    } else if (sortField === 'price') {
      const sorted = [...sortedDomains].sort((a, b) => a.price - b.price);
      setSortedDomains(sorted);
    } else {
      setSortedDomains(sortedDomains);
    }
  }, [sortField, sortOrder, sortedDomains]);

  const handleSortChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedValue = e.target.value;
    setSortField(selectedValue);
    setSortOrder(selectedValue === 'desc' ? 'desc' : 'asc');
  };

  return (
    <div className="container mx-auto p-4">
      {loading && <p>Loading domains...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {filteredDomains.length === 0 && !loading && !error && <p>No domains found.</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {filteredDomains.map(domain => (
          <div
            key={domain.name}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`Domain: ${domain.name}`}
          >
            <p className="text-xl font-semibold">{domain.name}</p>
            <p className="text-gray-700">Price: ${domain.price}</p>
            <p className="text-gray-700">Available: {domain.available ? 'Yes' : 'No'}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Filter:</label>
        <input
          type="text"
          className="px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter domain name"
          value={filterText}
          onChange={(e) => setSearchParams({ filter: e.target.value })}
        />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Sort:</label>
        <select
          className="px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={sortField}
          onChange={handleSortChange}
        >
          <option value="price" >Price</option>
          <option value="name" >Name</option>
        </select>
        <span className="text-sm">Order: {sortOrder}</span>
      </div>
    </div>
  );
};

export default DomainList;