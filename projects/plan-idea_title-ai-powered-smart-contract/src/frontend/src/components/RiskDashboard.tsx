import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface RiskAssessment {
  contractAddress: string;
  severity: number;
  riskScore: number;
  description: string;
}

interface RiskDashboardProps {
  initialRiskAssessments?: RiskAssessment[];
}

const RiskDashboard: React.FC<RiskDashboardProps> = ({ initialRiskAssessments = [] }) => {
  const [riskAssessments, setRiskAssessments] = useState<RiskAssessment[]>(initialRiskAssessments);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const filterContractAddress = searchParams.get('contractAddress') || '';
  const filterSeverity = searchParams.get('severity') || '0';

  useEffect(() => {
    // Simulate fetching data from an API
    const fetchData = async () => {
      try {
        const simulatedData: RiskAssessment[] = [
          { contractAddress: '0x123...', severity: 2, riskScore: 85, description: 'High Risk' },
          { contractAddress: '0x456...', severity: 1, riskScore: 60, description: 'Medium Risk' },
          { contractAddress: '0x789...', severity: 3, riskScore: 92, description: 'Critical Risk' },
          { contractAddress: '0x123...', severity: 1, riskScore: 50, description: 'Low Risk' },
        ];

        setRiskAssessments(simulatedData);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch risk assessments.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredRiskAssessments = riskAssessments.filter((assessment) => {
    if (!filterContractAddress) {
      return true;
    }
    return assessment.contractAddress.includes(filterContractAddress);
  });

  const severityToInt = (severity: number) => {
    switch (severity) {
      case 0: return 0;
      case 1: return 1;
      case 2: return 2;
      case 3: return 3;
      default: return 2;
    }
  }

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      {loading && <p className="text-center text-gray-500">Loading...</p>}
      {error && <p className="text-center text-red-500">{error}</p>}

      <div className="mb-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Contract Address:</label>
        <input
          type="text"
          className="rounded-md border border-gray-300 py-2 px-4 w-full max-w-2xl"
          placeholder="Enter contract address"
          value={filterContractAddress}
          onChange={(e) => setSearchParams({ contractAddress: e.target.value })}
          aria-label="Filter by contract address"
        />
      </div>

      <div className="mb-4 flex items-center justify-between">
        <label className="mr-2 text-sm font-medium">Severity:</label>
        <select
          id="severity"
          className="rounded-md border border-gray-300 py-2 px-4 w-full max-w-2xl"
          onChange={(e) => setSearchParams({ severity: e.target.value })}
          value={filterSeverity}
          aria-label="Filter by severity"
        >
          <option value="0">All</option>
          <option value="1">Low</option>
          <option value="2">Medium</option>
          <option value="3">High</option>
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4 mb-4">
        {filteredRiskAssessments.map((assessment) => (
          <div key={assessment.contractAddress} className="bg-white rounded-md shadow-sm p-4 hover:shadow-lg">
            <h3 className="text-lg font-semibold text-gray-800">{assessment.contractAddress}</h3>
            <p className="text-sm text-gray-600">Severity: {severityToInt(assessment.severity)}</p>
            <div className="progress-bar" style={{ width: `${(assessment.riskScore / 100) * 100}%` }}></div>
            <p className="text-gray-700">{assessment.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskDashboard;