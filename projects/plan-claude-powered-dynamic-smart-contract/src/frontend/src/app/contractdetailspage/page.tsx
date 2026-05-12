import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface ContractDetails {
  contractAddress: string;
  contractCode: string;
  vulnerabilityReports: VulnerabilityReport[];
}

interface VulnerabilityReport {
  severity: number;
  description: string;
  url: string;
}

const ContractDetailsPage = ({ contract }: ContractDetails) => {
  const { asPath } = useRouter();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    // Simulate fetching data from an API
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Loading Contract Details...</h1>
        <p className="text-gray-500">
          This page is loading contract details.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Error</h1>
        <p className="text-red-500">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-4xl font-bold mb-4">{contract.contractAddress}</h1>

      <div className="mb-6">
        <p className="text-xl font-semibold mb-2">Contract Code:</p>
        <pre className="bg-gray-100 p-4 rounded-md overflow-auto">
          <code className="text-sm whitespace-pre-wrap">
            {contract.contractCode}
          </code>
        </pre>
      </div>

      <div className="mb-6">
        <p className="text-xl font-semibold mb-2">Vulnerability Reports:</p>
        <ul className="list-disc list-inside mb-0">
          {contract.vulnerabilityReports.map((report) => (
            <li
              key={report.url}
              className="mb-2"
              aria-label={`Vulnerability report: ${report.description}`}
            >
              {report.severity} - {report.description}
              <a
                href={report.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700"
              >
                View Report
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ContractDetailsPage;