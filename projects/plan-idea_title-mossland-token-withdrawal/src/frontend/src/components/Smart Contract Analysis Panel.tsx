import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface SmartContractAnalysisResult {
  anomalyScore: number;
  detectedAnomalies: string[];
  vulnerabilities: string[];
  profileData: any;
}

interface SmartContractAnalysisPanelProps {
  contractAddress: string;
}

const SmartContractAnalysisPanel: React.FC<SmartContractAnalysisPanelProps> = ({ contractAddress }) => {
  const [searchParams] = useSearchParams();
  const analysisId = searchParams.get('analysisId');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisResults, setAnalysisResults] = useState<SmartContractAnalysisResult | null>(null);

  useEffect(() => {
    // Simulate fetching analysis data from an API
    const fetchData = async () => {
      try {
        // Replace with your actual API call
        const response = await fetch(`https://api.example.com/analysis/${analysisId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data: SmartContractAnalysisResult = await response.json();
        setAnalysisResults(data);
      } catch (error) {
        setError(`Failed to fetch analysis: ${error}`);
      } finally {
        setLoading(false);
      }
    };

    if (analysisId) {
      fetchData();
    } else {
      setError('Analysis ID is required.');
      setLoading(false);
    }
  }, [analysisId]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-center">Loading analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-red-700 text-xl">Error: {error}</div>
      </div>
    );
  }

  if (!analysisResults) {
    return (
      <div className="bg-gray-100 p-4 rounded-md shadow-md w-full max-w-md">
        <div className="text-center">No analysis data available.</div>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-md shadow-md w-full max-w-md">
      <h2 className="text-lg font-semibold mb-4">Smart Contract Analysis</h2>
      <p className="text-gray-700">Contract Address: {contractAddress}</p>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Anomaly Detection</h3>
        <p className="text-gray-700">Anomaly Score: {analysisResults.anomalyScore}</p>
        <p className="text-gray-700">Detected Anomalies: {analysisResults.detectedAnomalies.join(', ')}</p>
      </div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Smart Contract Profiling Data</h3>
        <p className="text-gray-700">Detailed data will be displayed here.</p>
        {/* Replace with actual profile data display */}
        <pre className="bg-gray-100 p-2 rounded-md overflow-auto">
          {JSON.stringify(analysisResults.profileData, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default SmartContractAnalysisPanel;