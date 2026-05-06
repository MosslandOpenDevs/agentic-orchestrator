import React, { useState, useEffect } from 'react';
import { useTailwind } from 'tailwind-rn';
import { WebSocket } from 'react-native-websockets';
import {
  Chart,
  Line,
  XAxis,
  YAxis,
  Legend,
  Tooltip,
} from 'react-native-chart-kit';

const Tailwind = useTailwind();

type PortfolioData = {
  assetBalances: { [key: string]: number };
  yieldPerformance: { [key: string]: number };
  riskScore: number;
};

type RiskAssessmentData = {
  vulnerabilityReport: string;
};

type ClaudeAgentData = {
  recommendations: string;
  riskAdjustment: number;
};

const PortfolioDashboard = () => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [riskScore, setRiskScore] = useState(0);
  const [claudeData, setClaudeData] = useState<ClaudeAgentData | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate fetching data from WebSocket and other sources
        await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate delay
        const mockPortfolioData: PortfolioData = {
          assetBalances: { ETH: 1.2, DAI: 100 },
          yieldPerformance: { ETH: 0.05, DAI: 0.01 },
          riskScore: 50,
        };
        setPortfolioData(mockPortfolioData);
        await new Promise(resolve => setTimeout(resolve, 1000));
        const mockClaudeData: ClaudeAgentData = {
          recommendations: 'Increase ETH allocation',
          riskAdjustment: -10,
        };
        setClaudeData(mockClaudeData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const chartData = {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [
      {
        data: [10, 15, 13],
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
      },
    ],
  };

  return (
    <div className={Tailwind.container}>
      <header className={Tailwind.header}>
        <h1 className={Tailwind.title}>DeFi Risk Assessment Dashboard</h1>
      </header>

      <main className={Tailwind.main}>
        {loading ? (
          <div className={Tailwind.loading}>
            Loading data...
          </div>
        ) : (
          <>
            <section className={Tailwind.section}>
              <h2>Portfolio Overview</h2>
              <div className={Tailwind.card}>
                <p>Asset Balances:</p>
                <p>ETH: {portfolioData?.assetBalances.ETH} </p>
                <p>DAI: {portfolioData?.assetBalances.DAI} </p>
                <p>Yield Performance:</p>
                <p>ETH: {portfolioData?.yieldPerformance.ETH} </p>
                <p>DAI: {portfolioData?.yieldPerformance.DAI} </p>
                <p>Risk Score: {riskScore}</p>
              </div>
            </section>

            <section className={Tailwind.section}>
              <h2>Risk Assessment</h2>
              <div className={Tailwind.card}>
                <p>Vulnerability Report:</p>
                <p>{claudeData?.recommendations}</p>
              </div>
            </section>

            <section className={Tailwind.section}>
              <h2>Yield Chart</h2>
              <Chart
                data={chartData}
                width={350}
                height={200}
                padding={{ left: 10, right: 10, top: 20, bottom: 20 }}
                chartType="line"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.8)',
                }}
              />
            </section>
          </>
        )}
      </main>
    </div>
  );
};

export default PortfolioDashboard;