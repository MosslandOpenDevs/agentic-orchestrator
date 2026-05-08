import React, { useState, useEffect } from 'react';

interface StrategyConfig {
  [key: string]: number;
}

interface StrategyConfiguratorProps {
  initialConfig?: StrategyConfig;
  onSubmit?: (config: StrategyConfig) => void;
}

const StrategyConfigurator: React.FC<StrategyConfiguratorProps> = ({
  initialConfig = {},
  onSubmit,
}) => {
  const [config, setConfig] = useState<StrategyConfig>({ ...initialConfig });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement> | React.ChangeEvent<HTMLSelectElement>,
    key: string
  ) => {
    const value = event.target.value;
    setConfig((prevConfig) => {
      const newConfig = { ...prevConfig };
      newConfig[key] = parseFloat(value) || 0;
      return newConfig;
    });
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (onSubmit) {
        onSubmit(config);
      }
    } catch (err) {
      setError('An error occurred while submitting the configuration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // No need for complex logic here, just updating state is fine.
  }, [config]);

  return (
    <div className="max-w-md mx-auto p-4 rounded-lg shadow-md overflow-hidden">
      {error && <p className="text-red-500 p-2 rounded-md mb-2">{error}</p>}
      <form onSubmit={handleSubmit} aria-label="Strategy Configuration">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(config).map(([key, value]) => (
            <div key={key} className="relative">
              <label
                htmlFor={key}
                className="text-sm font-medium text-gray-700 mb-2"
                aria-label={`Parameter: ${key}`}
              >
                {key}
              </label>
              <input
                type="number"
                id={key}
                name={key}
                value={value.toString()}
                onChange={(event) => handleChange(event, key)}
                className="w-full p-3 rounded-md border border-gray-300 text-gray-700 focus:outline-none focus:border-blue-500"
                inputMode="numeric"
              />
            </div>
          ))}
        </div>
        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full"
          disabled={loading}
        >
          {loading ? 'Submitting...' : 'Save Configuration'}
        </button>
      </form>
    </div>
  );
};

export default StrategyConfigurator;