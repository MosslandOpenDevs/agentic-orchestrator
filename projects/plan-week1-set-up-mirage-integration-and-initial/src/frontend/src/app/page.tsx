import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';
import { StrategyList } from './components/StrategyList';
import { SimulationResultDisplay } from './components/SimulationResultDisplay';
import { StrategyConfigurator } from './components/StrategyConfigurator';
import { useOpenAI } from './hooks/useOpenAI';
import { useDuneAnalytics } from './hooks/useDuneAnalytics';
import { WebSocketClient } from './utils/WebSocketClient';
import { Card, CardHeader, CardBody, CardFooter, Button, Typography, Flex, Divider } from './ui/components';
import { useDarkMode } from './hooks/useDarkMode';

interface DAOStrategy {
  id: string;
  name: string;
  description: string;
  parameters: any;
}

const Dashboard = () => {
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('agentId') || 'defaultAgent';
  const [simulationResults, setSimulationResults] = useState<SimulationResultDisplay[]>([]);
  const [selectedResult, setSelectedResult] = useState<SimulationResultDisplay | null>(null);
  const [strategy, setStrategy] = useState<DAOStrategy | null>(null);
  const { data: openaiData, error: openaiError } = useOpenAI();
  const { data: duneData } = useDuneAnalytics();
  const wsClient = new WebSocketClient();

  const darkMode = useDarkMode();

  useEffect(() => {
    if (openaiData) {
      console.log('OpenAI Data:', openaiData);
    }
    if (openaiError) {
      console.error('OpenAI Error:', openaiError);
    }
  }, [openaiData, openaiError]);

  useEffect(() => {
    if (duneData) {
      console.log('Dune Data:', duneData);
    }
  }, [duneData]);

  useEffect(() => {
    wsClient.connect();
  }, []);

  const handleSimulationResultClick = (result: SimulationResultDisplay) => {
    setSelectedResult(result);
  };

  const handleStrategyChange = (newStrategy: DAOStrategy) => {
    setStrategy(newStrategy);
  };

  const simulate = async () => {
    console.log('Simulating...');
    // Placeholder for simulation logic
    await new Promise(resolve => setTimeout(resolve, 2000));
    setSimulationResults([
      { id: 'result1', name: 'Result 1', value: Math.random() },
      { id: 'result2', name: 'Result 2', value: Math.random() },
    ]);
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <header className="bg-gray-100 p-4 flex items-center justify-between">
        <Typography level={2} className="text-xl font-bold">
          Plan: week1
        </Typography>
      </header>

      <main className="flex-1 p-4">
        <Card className="mb-4">
          <CardHeader className="bg-gray-100 p-4">
            <Typography level={2} className="text-lg font-bold">
              Simulation Dashboard
            </Typography>
          </CardHeader>
          <CardBody>
            {simulationResults.length === 0 ? (
              <Typography className="text-center p-4">
                No simulation results available.
              </Typography>
            ) : (
              <StrategyList
                results={simulationResults}
                onResultClick={handleSimulationResultClick}
              />
            )}
          </CardBody>
          <CardFooter>
            <Button onClick={simulate} variant="primary">
              Simulate
            </Button>
          </CardFooter>
        </Card>

        <Card className="mb-4">
          <CardHeader className="bg-gray-100 p-4">
            <Typography level={2} className="text-lg font-bold">
              Strategy Configurator
            </Typography>
          </CardHeader>
          <CardBody>
            {strategy && (
              <StrategyConfigurator
                strategy={strategy}
                onStrategyChange={handleStrategyChange}
              />
            )}
          </CardBody>
        </Card>

        {selectedResult && (
          <Card className="mb-4">
            <CardHeader className="bg-gray-100 p-4">
              <Typography level={2} className="text-lg font-bold">
                Simulation Result: {selectedResult.name}
              </Typography>
            </CardHeader>
            <CardBody>
              <Typography className="text-lg font-bold">Value: {selectedResult.value}</Typography>
              <Typography>
                Detailed result data goes here.
              </Typography>
            </CardBody>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Dashboard;

// components/StrategyList.tsx
import React from 'react';
import { SimulationResultDisplay } from '../components/SimulationResultDisplay';

interface StrategyListProps {
  results: SimulationResultDisplay[];
  onResultClick: (result: SimulationResultDisplay) => void;
}

export const StrategyList = ({ results, onResultClick }: StrategyListProps) => {
  return (
    <div className="grid grid-cols-1 gap-4">
      {results.map((result) => (
        <div
          key={result.id}
          className="bg-gray-100 p-4 rounded-md hover:shadow-md cursor-pointer"
          onClick={() => onResultClick(result)}
        >
          <Typography level={4} className="font-bold">{result.name}</Typography>
          <Typography className="text-sm">{result.value}</Typography>
        </div>
      ))}
    </div>
  );
};

// components/SimulationResultDisplay.tsx
interface SimulationResultDisplay {
  id: string;
  name: string;
  value: number;
}

export const SimulationResultDisplay = ({ id, name, value }: SimulationResultDisplay) => {
  return (
    <div className="bg-white p-4 rounded-md shadow-md">
      <Typography level={4} className="font-bold">{name}</Typography>
      <Typography>{value}</Typography>
    </div>
  );
};

// components/StrategyConfigurator.tsx
import React from 'react';

interface StrategyConfiguratorProps {
  strategy: any;
  onStrategyChange: (newStrategy: any) => void;
}

export const StrategyConfigurator = ({ strategy, onStrategyChange }: StrategyConfiguratorProps) => {
  return (
    <div className="p-4">
      <Typography level={2} className="font-bold">
        Configure Strategy
      </Typography>
      {/* Add your strategy configuration components here */}
      <Typography>Strategy ID: {strategy.id}</Typography>
      <Typography>Strategy Name: {strategy.name}</Typography>
      <Button onClick={() => onStrategyChange(strategy)}>Update Strategy</Button>
    </div>
  );
};

// utils/WebSocketClient.tsx
import { WebSocket } from 'ws';

const ws = new WebSocket('ws://localhost:8080'); // Replace with your WebSocket server URL

export class WebSocketClient {
  private ws: WebSocket;

  constructor() {
    this.ws = new WebSocket('ws://localhost:8080');

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  connect() {
    if (!this.ws.readyState) {
      this.ws.connect();
    }
  }

  disconnect() {
    this.ws.close();
  }
}

// hooks/useOpenAI.tsx
import { useState } from 'react';

interface UseOpenAIResult {
  data?: any;
  error?: string;
}

export const useOpenAI = (): UseOpenAIResult => {
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await fetch('https://api.openai.com/v1/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer YOUR_OPENAI_API_KEY',
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          prompt: 'Write a short summary of the plan.',
          max_tokens: 50,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const json = await response.json();
      setData(json.choices[0].text);
      setError(null);
    } catch (error) {
      setError(error.message);
      setData(null);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return { data, error };
};

// hooks/useDuneAnalytics.tsx
import { useState, useEffect } from 'react';

interface UseDuneAnalyticsResult {
  data?: any;
  error?: string;
}

export const useDuneAnalytics = (): UseDuneAnalyticsResult => {
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDuneData = async () => {
      try {
        const response = await fetch('https://dune.sh/api/v1/queries/784679917646489920');
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const json = await response.json();
        setData(json);
        setError(null);
      } catch (error) {
        setError(error.message);
        setData(null);
      }
    };

    fetchDuneData();
  }, []);

  return { data, error };
};

// hooks/useDarkMode.tsx
import { useState, useEffect } from 'react';

const useDarkMode = () => {
  const [theme, setTheme] = useState<string>('light');

  useEffect(() => {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  }, []);

  return theme;
};

// ui/components/Card.tsx
import React from 'react';

export const Card = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="max-w-md rounded-lg shadow-md overflow-hidden">
      {children}
    </div>
  );
};

// ui/components/Typography.tsx
import React from 'react';

export const Typography = ({
  children,
  level,
  className = '',
}: {
  children: React.ReactNode;
  level?: number;
  className?: string;
}) => {
  return (
    <span className={`text-sm ${className} font-medium ${level ? `text-${level}` : ''}`}>
      {children}
    </span>
  );
};

// ui/components/Flex.tsx
import React from 'react';

export const Flex = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex">
      {children}
    </div>
  );
};

// ui/components/Divider.tsx
import React from 'react';

export const Divider = () => {
  return <div className="h-[1px] bg-gray-200 w-full"></div>;
};

// styles/globals.css
body {
  margin: 0;
  font-family: -webkit-font-smoothing: antialiased;
  -webkit-font-smoothing: antialiased;
  font-family: 'Roboto', sans-serif;
}

/* Skips initial fast painting for smoother scroll experience */
html {
  scroll-behavior: smooth;
}

/* Changes the default font */
body,
html {
  font-size: 16px;
}