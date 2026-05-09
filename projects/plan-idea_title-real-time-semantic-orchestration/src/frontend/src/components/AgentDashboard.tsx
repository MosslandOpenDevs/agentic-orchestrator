import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

// Define interfaces for data models
interface Agent {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  config: any; // Replace 'any' with a more specific type if possible
}

interface AgentDashboardProps {
  initialAgents?: Agent[];
}

const AgentDashboard: React.FC<AgentDashboardProps> = ({ initialAgents = [] }) => {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    // Simulate fetching agents from an API
    const fetchData = async () => {
      try {
        const data = await new Promise<Agent[]>((resolve) => {
          setTimeout(() => {
            resolve(
              [
                { id: '1', name: 'Agent A', status: 'active', config: { setting1: 'value1' } },
                { id: '2', name: 'Agent B', status: 'inactive', config: { setting1: 'value2' } },
              ]
            );
          }, 1000);
        });
        setAgents(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch agents.');
        setLoading(false);
        toast(`Error fetching agents: ${err}`, { type: 'error' });
      }
    };

    fetchData();
  }, []);

  const handleAgentStatusChange = (id: string, newStatus: 'active' | 'inactive') => {
    setAgents(agents.map((agent) => (agent.id === id ? { ...agent, status: newStatus } : agent));
    toast(`Agent ${id} status updated to ${newStatus}`, { type: 'success' });
  };

  if (loading) {
    return <div>Loading agents...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Agent Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition duration-300 ease-in-out"
            aria-label={`Agent ${agent.name}`}
          >
            <h2 className="text-xl font-semibold mb-2">{agent.name}</h2>
            <p className="text-gray-700">Status: {agent.status}</p>
            <button
              onClick={() => handleAgentStatusChange(agent.id, agent.status === 'active' ? 'inactive' : 'active')}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4"
              aria-label={`Change status of ${agent.name}`}
            >
              Toggle Status
            </button>
            <button
              onClick={() => {
                toast(`Edit Agent ${agent.name}`, { type: 'info' });
              }}
              className="text-blue-500 hover:text-blue-700 font-bold mt-2"
              aria-label={`View Agent Details for ${agent.name}`}
            >
              View Details
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentDashboard;