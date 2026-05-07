import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface RiskTolerance {
  id: number;
  name: 'Low', 'Medium', 'High';
}

interface Protocol {
  id: number;
  name: string;
  description: string;
}

interface ConfigurationState {
  riskTolerance: RiskTolerance;
  protocol: Protocol;
  yieldTarget: number;
  loading: boolean;
  error: string | null;
}

const YieldFarmingStrategyConfiguration: React.FC<
  {
    protocols: Protocol[];
    onConfigurationChange: (
      riskTolerance: RiskTolerance,
      protocol: Protocol,
      yieldTarget: number
    ) => void;
  }
> = ({ protocols, onConfigurationChange }) => {
  const [configuration, setConfiguration] = useState<ConfigurationState>({
    riskTolerance: { id: 1, name: 'Medium' },
    protocol: protocols[0],
    yieldTarget: 10,
    loading: true,
    error: null,
  });
  const { addToast } = useToast();

  useEffect(() => {
    // Simulate fetching data (replace with actual API call)
    setTimeout(() => {
      setConfiguration({
        riskTolerance: { id: 1, name: 'Medium' },
        protocol: protocols[0],
        yieldTarget: 10,
        loading: false,
        error: null,
      });
    }, 1000);
  }, []);

  const handleRiskToleranceChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const selectedValue = event.target.value;
    const riskTolerance = protocols.find(
      (p) => p.name === selectedValue
    )!;
    setConfiguration({
      ...configuration,
      riskTolerance: riskTolerance,
    });
    onConfigurationChange(riskTolerance, configuration.protocol, configuration.yieldTarget);
  };

  const handleProtocolChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const selectedValue = event.target.value;
    const protocol = protocols.find((p) => p.id === parseInt(selectedValue));
    if (protocol) {
      setConfiguration({
        ...configuration,
        protocol: protocol,
      });
      onConfigurationChange(configuration.riskTolerance, protocol, configuration.yieldTarget);
    } else {
      addToast('Invalid protocol selected', { toastId: 'protocolError', appearance: 'error' });
    }
  };

  const handleYieldTargetChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const target = parseInt(event.target.value);
    if (!isNaN(target)) {
      setConfiguration({
        ...configuration,
        yieldTarget: target,
      });
      onConfigurationChange(configuration.riskTolerance, configuration.protocol, target);
    } else {
      addToast('Please enter a valid yield target', { toastId: 'yieldError', appearance: 'error' });
    }
  };

  return (
    <div className="bg-gray-100 p-8 rounded-lg shadow-md w-full max-w-4xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Yield Farming Strategy Configuration</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Risk Tolerance</label>
          <select
            className="bg-gray-100 border rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2"
            value={configuration.riskTolerance.name}
            onChange={handleRiskToleranceChange}
            aria-label="Select Risk Tolerance"
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Protocol</label>
          <select
            className="bg-gray-100 border rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2"
            value={configuration.protocol.name}
            onChange={handleProtocolChange}
            aria-label="Select Protocol"
          >
            {protocols.map((protocol) => (
              <option key={protocol.id} value={protocol.id.toString()}>
                {protocol.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Yield Target (APY)</label>
        <input
          type="number"
          className="bg-gray-100 border rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2"
          value={configuration.yieldTarget.toString()}
          onChange={handleYieldTargetChange}
          aria-label="Enter Yield Target"
        />
      </div>

      {configuration.loading && <p className="text-center mt-6 p-4 bg-gray-200 rounded-md">Loading...</p>}
      {configuration.error && (
        <p className="text-center mt-6 p-4 bg-red-200 rounded-md">
          Error: {configuration.error}
        </p>
      )}
    </div>
  );
};

export default YieldFarmingStrategyConfiguration;