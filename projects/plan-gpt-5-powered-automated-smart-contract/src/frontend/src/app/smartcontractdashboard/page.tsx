import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface Contract {
  id: string;
  name: string;
  address: string;
  vulnerabilityReports: VulnerabilityReport[];
  riskAssessment: RiskAssessment;
}

interface VulnerabilityReport {
  id: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  timestamp: string;
}

interface RiskAssessment {
  overallRisk: 'high' | 'medium' | 'low';
  details: string;
}

const SmartContractDashboard = () => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        // Simulate fetching data from an API
        const dummyContracts: Contract[] = [
          {
            id: 'contract1',
            name: 'Contract A',
            address: '0x...',
            vulnerabilityReports: [
              { id: 'report1', severity: 'high', description: 'Critical vulnerability', timestamp: '2024-01-01' },
            ],
            riskAssessment: { overallRisk: 'medium', details: 'Moderate risk due to complexity' },
          },
          {
            id: 'contract2',
            name: 'Contract B',
            address: '0x...',
            vulnerabilityReports: [],
            riskAssessment: { overallRisk: 'low', details: 'Low risk, minimal complexity' },
          },
        ];
        setContracts(dummyContracts);
        setLoading(false);
      } catch (err) {
        setError('Failed to load contracts.');
        console.error('Error fetching contracts:', err);
        setLoading(false);
      }
    };

    fetchContracts();
  }, []);

  const handleFilter = (filterValue: string) => {
    setSearchParams({ filter: filterValue });
  };

  return (
    <div className="container mx-auto p-4">
      {loading && <p>Loading contracts...</p>}
      {error && <p className="text-red-500">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {contracts.map((contract) => (
          <div
            key={contract.id}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300"
            aria-label={`Contract ${contract.name}`}
          >
            <h3>{contract.name}</h3>
            <p>Address: {contract.address}</p>
            {contract.vulnerabilityReports.length > 0 && (
              <div className="mt-4">
                <h4>Vulnerability Reports</h4>
                <ul>
                  {contract.vulnerabilityReports.map((report) => (
                    <li
                      key={report.id}
                      className="mb-2"
                      aria-label={`Vulnerability Report ${report.description}`}
                    >
                      Severity: {report.severity}, Description: {report.description}, Timestamp: {report.timestamp}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {contract.riskAssessment && (
              <div className="mt-4">
                <h4>Risk Assessment</h4>
                <p>Overall Risk: {contract.riskAssessment.overallRisk}</p>
                <p>{contract.riskAssessment.details}</p>
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="mt-4">
        <label htmlFor="filter" className="sr-only">Filter Contracts</label>
        <input
          type="text"
          id="filter"
          className="px-3 py-2 border rounded-md"
          placeholder="Search contracts..."
          onKeyUp={(e) => handleFilter(e.target.value)}
        />
      </div>
    </div>
  );
};

export default SmartContractDashboard;