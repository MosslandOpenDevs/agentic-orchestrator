import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { WebSocket } from 'ws';

// Placeholder data - replace with actual data from API calls
interface SmartContract {
  id: string;
  name: string;
  status: 'pending' | 'approved' | 'rejected';
}

interface VulnerabilityReport {
  id: string;
  contractId: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  riskAssessment: string;
}

interface RiskAssessment {
  id: string;
  reportId: string;
  assessment: string;
}

type SmartContracts = SmartContract[];
type VulnerabilityReports = VulnerabilityReport[];
type RiskAssessments = RiskAssessment[];

const Dashboard = () => {
  const [smartContracts, setSmartContracts] = useState<SmartContracts>([]);
  const [vulnerabilityReports, setVulnerabilityReports] = useState<VulnerabilityReports>([]);
  const [riskAssessments, setRiskAssessments] = useState<RiskAssessments>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  // Mock API calls - replace with actual API calls
  useEffect(() => {
    const fetchSmartContracts = async () => {
      const data = [
        { id: '1', name: 'MosslandToken', status: 'pending' },
        { id: '2', name: 'NFTContract', status: 'pending' },
      ];
      setSmartContracts(data);
    };

    const fetchVulnerabilityReports = async () => {
      const data = [
        { id: '101', contractId: '1', description: 'Reentrancy Vulnerability', severity: 'high' },
        { id: '102', contractId: '2', description: 'Integer Overflow', severity: 'medium' },
      ];
      setVulnerabilityReports(data);
    };

    const fetchRiskAssessments = async () => {
      const data = [
        { id: '201', reportId: '101', assessment: 'High risk, immediate remediation required' },
        { id: '202', reportId: '102', assessment: 'Medium risk, review recommended' },
      ];
      setRiskAssessments(data);
    };

    fetchSmartContracts();
    fetchVulnerabilityReports();
    fetchRiskAssessments();
  }, []);

  // Placeholder WebSocket connection - replace with actual WebSocket implementation
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8080'); // Replace with your WebSocket server URL

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      // Handle incoming updates from the WebSocket server
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className={`min-h-screen dark-mode ${darkMode ? 'dark-mode' : ''}`}>
      <header className="bg-gray-800 text-white p-4">
        <h1>Singularity - Smart Contract Vulnerability Dashboard</h1>
      </header>

      <main className="p-4 flex">
        <aside className="bg-gray-700 p-4 w-64">
          {/* Sidebar - Navigation */}
          <h2>Navigation</h2>
          <ul>
            <li><a href="#" onClick={() => setDarkMode(!darkMode)}>Toggle Dark Mode</a></li>
            <li>Smart Contracts</li>
            <li>Vulnerability Reports</li>
            <li>Risk Assessments</li>
          </ul>
        </aside>

        <div className="flex-grow ml-4">
          {/* Main Content */}
          <section className="mb-4">
            <h2>Smart Contracts</h2>
            <div className="grid grid-cols-1 gap-4">
              {smartContracts.map((contract) => (
                <div key={contract.id} className={`bg-gray-800 p-4 rounded-md shadow-md`}>
                  <h3>{contract.name}</h3>
                  <p>Status: {contract.status}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mb-4">
            <h2>Vulnerability Reports</h2>
            <div className="grid grid-cols-1 gap-4">
              {vulnerabilityReports.map((report) => (
                <div key={report.id} className={`bg-gray-800 p-4 rounded-md shadow-md`}>
                  <h3>{report.contractId} - {report.description}</h3>
                  <p>Severity: {report.severity}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="mb-4">
            <h2>Risk Assessments</h2>
            <div className="grid grid-cols-1 gap-4">
              {riskAssessments.map((assessment) => (
                <div key={assessment.id} className={`bg-gray-800 p-4 rounded-md shadow-md`}>
                  <h3>{assessment.reportId}</h3>
                  <p>Assessment: {assessment.assessment}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;