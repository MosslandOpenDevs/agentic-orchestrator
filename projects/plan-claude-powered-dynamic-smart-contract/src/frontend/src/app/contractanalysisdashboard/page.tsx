import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface ContractAnalysisData {
  vulnerabilityScore: number;
  remediationSuggestions: string[];
  vulnerabilityReports: string[];
}

interface ContractAnalysisDashboardProps {
  contractAddress: string;
}

const ContractAnalysisDashboard: React.FC<ContractAnalysisDashboardProps> = ({ contractAddress }) => {
  const [data, setData] = useState<ContractAnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate fetching data from an API
        const response = await fetch(`https://api.example.com/contract-analysis?address=${contractAddress}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const result = await response.json() as ContractAnalysisData;
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [contractAddress]);

  if (loading) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 aria-label="Contract Analysis Dashboard">
          Analyzing Contract: {contractAddress}
        </h1>
        <p>Loading analysis data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 aria-label="Contract Analysis Dashboard">
          Error: {error}
        </h1>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 aria-label="Contract Analysis Dashboard">
          No data available for {contractAddress}
        </h1>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 aria-label="Contract Analysis Dashboard">Contract Analysis for {contractAddress}</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h2 className="text-lg font-bold mb-2">Vulnerability Score</h2>
          <p className="text-xl font-semibold">Score: {data.vulnerabilityScore}</p>
          <p className="text-gray-600">
            (This represents the overall risk level of the contract.)
          </p>
        </div>

        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h2 className="text-lg font-bold mb-2">Remediation Suggestions</h2>
          {data.remediationSuggestions.map((suggestion, index) => (
            <p key={index} className="text-gray-700">{suggestion}</p>
          ))}
        </div>

        <div className="bg-gray-100 p-4 rounded-md shadow-md">
          <h2 className="text-lg font-bold mb-2">Vulnerability Reports</h2>
          {data.vulnerabilityReports.map((report, index) => (
            <p key={index} className="text-gray-700">{report}</p>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ContractAnalysisDashboard;