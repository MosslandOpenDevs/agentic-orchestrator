import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ethers } from 'ethers';

// Define interfaces for data
interface ContractDetails {
  name: string;
  abi: any[];
  address: string;
  vulnerabilityReports: VulnerabilityReport[];
  riskAssessment: RiskAssessment;
}

interface VulnerabilityReport {
  id: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  date: string;
}

interface RiskAssessment {
  overallRisk: 'low' | 'medium' | 'high';
  details: string[];
}

const ContractDetailsPage = ({ contract }: { contract: ContractDetails }) => {
  const { router } = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!contract) {
      router.push('/404');
      return;
    }
    setLoading(true);
    // Simulate fetching data - replace with actual API calls
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, [contract, router]);

  if (loading) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Contract Details</h1>
        <p className="text-gray-500">Loading contract details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Error</h1>
        <p className="text-red-500">Failed to load contract details: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">{contract.name}</h1>

      {/* Contract ABI Display */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Contract ABI</h2>
        <pre className="bg-gray-100 p-2 rounded-md">
          {JSON.stringify(contract.abi, null, 2)}
        </pre>
      </div>

      {/* Vulnerability Report Listing */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Vulnerability Reports</h2>
        {contract.vulnerabilityReports.map((report) => (
          <div key={report.id} className="mb-2">
            <p className="text-gray-600">{report.description}</p>
            <p className="text-sm font-semibold text-green-500">{report.severity}</p>
            <p className="text-gray-500">{report.date}</p>
          </div>
        ))}
      </div>

      {/* Risk Assessment Visualization */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Risk Assessment</h2>
        <p className="text-gray-600">Overall Risk: {contract.riskAssessment.overallRisk}</p>
        <ul className="list-disc list-inside text-gray-600 mt-2">
          {contract.riskAssessment.details.map((detail) => (
            <li key={detail} className="text-sm">{detail}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ContractDetailsPage;