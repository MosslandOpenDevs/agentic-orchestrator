import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface SmartContract {
  id: string;
  name: string;
  address: string;
}

interface VulnerabilityReport {
  severity: string;
  description: string;
  vulnerabilityId: string;
}

interface RiskAssessment {
  score: number;
  description: string;
}

interface SmartContractDashboardProps {
  contracts: SmartContract[];
  vulnerabilityReports: VulnerabilityReport[];
  riskAssessments: RiskAssessment[];
}

const SmartContractDashboard: React.FC<SmartContractDashboardProps> = ({
  contracts,
  vulnerabilityReports,
  riskAssessments,
}) => {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (contracts.length === 0 && vulnerabilityReports.length === 0 && riskAssessments.length === 0) {
      router.push('/404');
    }
    setLoading(false);
  }, [contracts, vulnerabilityReports, riskAssessments, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p>Loading smart contracts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Smart Contract Dashboard</h1>

      {/* Contract Listing */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Contracts</h2>
        <ul className="list-disc space-y-2">
          {contracts.map((contract) => (
            <li
              key={contract.id}
              className="hover:underline cursor-pointer"
              aria-label={`Contract: ${contract.name} (${contract.address})`}
            >
              {contract.name} - {contract.address}
            </li>
          ))}
        </ul>
      </div>

      {/* Vulnerability Report Display */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Vulnerability Reports</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Description</th>
              <th>Contract</th>
            </tr>
          </thead>
          <tbody>
            {vulnerabilityReports.map((report) => (
              <tr key={report.vulnerabilityId} aria-label={`Vulnerability Report for ${report.description}`}>
                <td>{report.severity}</td>
                <td>{report.description}</td>
                <td>{contracts.find((c) => c.id === report.vulnerabilityId)?.name || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Risk Assessment Visualization */}
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">Risk Assessments</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Score</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {riskAssessments.map((assessment) => (
              <tr key={assessment.score} aria-label={`Risk Assessment: ${assessment.description}`}>
                <td>{assessment.score}</td>
                <td>{assessment.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SmartContractDashboard;