import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useSearchParams } from 'next/searchparams';

interface ContractAnalysisResult {
  vulnerabilityScore: number;
  remediationSuggestions: string[];
  detailedReport: string;
}

interface ContractAnalysisDashboardProps {
  contractAddress: string;
}

const ContractAnalysisDashboard: React.FC<ContractAnalysisDashboardProps> = ({ contractAddress }) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ContractAnalysisResult | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const results = await fetchAnalysisData(contractAddress);
        setAnalysisResult(results);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch analysis data.');
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [contractAddress]);

  const handleReportView = () => {
    router.push(`/report/${contractAddress}`);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Contract Analysis</h1>
        <p className="text-gray-600">Loading analysis results for contract {contractAddress}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Error</h1>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <div className="container mx-auto p-4 text-center">
        <h1 className="text-3xl font-bold mb-4">No Analysis Data</h1>
        <p className="text-gray-600">Could not retrieve analysis results.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Contract Analysis - {contractAddress}</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-2">Vulnerability Score</h2>
          <p className="text-gray-600 mb-2">Score: {analysisResult.vulnerabilityScore}</p>
          <p className="text-gray-600">Overall risk assessment based on the score.</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-2">Remediation Suggestions</h2>
          <ul className="list-disc pl-4 mb-2">
            {analysisResult.remediationSuggestions.map((suggestion, index) => (
              <li key={index} className="mb-1">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-xl font-semibold mb-2">Detailed Report</h2>
          <pre className="text-gray-800 whitespace-pre-wrap">
            {analysisResult.detailedReport}
          </pre>
          <button
            onClick={handleReportView}
            className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            aria-label="View Detailed Report"
          >
            View Detailed Report
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContractAnalysisDashboard;

// Mock fetchAnalysisData function for demonstration
async function fetchAnalysisData(contractAddress: string): Promise<ContractAnalysisResult> {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  if (contractAddress === '0x123') {
    return {
      vulnerabilityScore: 75,
      remediationSuggestions: ['Implement proper input validation', 'Use secure coding practices'],
      detailedReport: 'This contract exhibits several vulnerabilities, including potential integer overflows and lack of access control.  Further investigation is recommended.'
    };
  } else if (contractAddress === '0x456') {
    return {
      vulnerabilityScore: 30,
      remediationSuggestions: ['Review smart contract logic', 'Conduct thorough security audit'],
      detailedReport: 'The contract appears relatively secure, but a detailed security audit is still recommended.'
    };
  }
  else {
    throw new Error('Contract not found or analysis data unavailable.');
  }
}