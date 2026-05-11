import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface ContractDetails {
  name: string;
  code: string;
  riskScore: number;
  vulnerabilities: Vulnerability[];
}

interface Vulnerability {
  id: string;
  name: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
}

const ContractDetailsPage = ({ contract }: { contract: ContractDetails }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (contract.code === null || contract.riskScore === null || contract.vulnerabilities === null) {
      setError('Failed to load contract details.');
      return;
    }

    setLoading(false);
  }, [contract]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading contract details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-4">{contract.name}</h1>

      <div className="mb-4">
        <p className="text-gray-700">Risk Score: {contract.riskScore}</p>
        <div className="relative">
          <div className="h-20 w-full bg-red-500 rounded-full" style={{ transform: 'scaleY(0.5)' }}></div>
          <div className="absolute left-1/2 bottom-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-red-400 rounded-full w-16 h-16" aria-label="Risk Score Indicator"></div>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-gray-700">Contract Code:</p>
        <pre className="bg-gray-100 p-2 rounded-md">
          <code className="whitespace-pre-wrap">{contract.code}</code>
        </pre>
      </div>

      <h2 className="text-2xl font-bold mb-2">Vulnerabilities</h2>
      {contract.vulnerabilities.length === 0 ? (
        <p className="text-gray-600">No vulnerabilities found.</p>
      ) : (
        <ul className="list-disc list-inside mb-2">
          {contract.vulnerabilities.map((vulnerability) => (
            <li
              key={vulnerability.id}
              className="mb-1"
              aria-label={`Vulnerability: ${vulnerability.name}`}
            >
              {vulnerability.name} - Severity: {vulnerability.severity} - {vulnerability.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ContractDetailsPage;