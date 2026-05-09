import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface Domain {
  name: string;
  nft?: string; // Optional NFT ID
}

interface DomainDashboardProps {
  domains: Domain[];
}

const DomainDashboard: React.FC<DomainDashboardProps> = ({ domains }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const domainName = searchParams.get('domain');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (domainName) {
      const filteredDomains = domains.filter((domain) => domain.name === domainName);
      if (filteredDomains.length === 0) {
        setError('Domain not found.');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [domains, domainName]);

  if (loading) {
    return (
      <div className="p-4 text-center">
        <p>Loading domains...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      {domains.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {domains.map((domain) => (
            <DomainCard key={domain.name} domain={domain} />
          ))}
        </div>
      )}
    </div>
  );
};

interface DomainCardProps {
  domain: Domain;
}

const DomainCard: React.FC<DomainCardProps> = ({ domain }) => {
  const { name, nft } = domain;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="p-4 flex items-center">
        <h3 className="text-xl font-semibold">{name}</h3>
        {nft && (
          <div className="ml-4">
            <p className="text-sm font-semibold text-blue-500">NFT:</p>
            <p className="text-base">{nft}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DomainDashboard;