import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface ContractDetails {
  name: string;
  code: string;
  metadata: {
    address: string;
    contractType: string;
    deployedAt: string;
    version: string;
  };
  vulnerabilityReports?: VulnerabilityReport[];
}

interface VulnerabilityReport {
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  reportId: string;
}

const ContractDetailsPage = ({ contract }: { contract: ContractDetails }) => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (contract.code) {
      setLoading(false);
    }
  }, [contract.code]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Contract Details</h1>
        <p className="text-gray-600">Loading contract details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Error</h1>
        <p className="text-red-600">Error loading contract details: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{contract.name}</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 border border-gray-300 rounded-md">
          <p className="text-gray-700 mb-2">Contract Code:</p>
          <pre className="bg-gray-100 p-2 rounded-md">
            {contract.code}
          </pre>
        </div>

        <div className="p-4 border border-gray-300 rounded-md">
          <p className="text-gray-700 mb-2">Vulnerability Reports:</p>
          {contract.vulnerabilityReports && contract.vulnerabilityReports.length > 0 ? (
            <ul>
              {contract.vulnerabilityReports.map((report) => (
                <li key={report.reportId} className="p-2 border border-gray-300 rounded-md mb-2">
                  <p className="text-gray-700">Severity: {report.severity}</p>
                  <p className="text-gray-700">Description: {report.description}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600">No vulnerability reports found.</p>
          )}
        </div>

        <div className="p-4 border border-gray-300 rounded-md">
          <p className="text-gray-700 mb-2">Contract Metadata:</p>
          <p className="text-gray-700">Address: {contract.metadata.address}</p>
          <p className="text-gray-700">Contract Type: {contract.metadata.contractType}</p>
          <p className="text-gray-700">Deployed At: {contract.metadata.deployedAt}</p>
          <p className="text-gray-700">Version: {contract.metadata.version}</p>
        </div>
      </div>
    </div>
  );
};

export default ContractDetailsPage;