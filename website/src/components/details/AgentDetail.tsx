'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient } from '@/lib/api';
import type { ModalData } from '../modals/ModalProvider';
import { ScoreGauge } from '../visualization/ScoreGauge';
import { TerminalBadge } from '../TerminalWindow';

interface AgentDetailProps {
  data: ModalData;
}

interface AgentData {
  id: string;
  name: string;
  role: string;
  phase: string;
  personality: {
    creativity: number;
    analytical: number;
    risk_tolerance: number;
    collaboration: number;
  };
  description?: string;
  handle?: string;
}

export function AgentDetail({ data }: AgentDetailProps) {
  const { t } = useI18n();
  const [agent, setAgent] = useState<AgentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgent() {
      setLoading(true);
      setError(null);

      // If full agent data is passed in, use it
      if (data.name && data.role && data.personality) {
        setAgent(data as unknown as AgentData);
        setLoading(false);
        return;
      }

      try {
        const response = await ApiClient.getAgents();
        if (response.data) {
          const found = response.data.agents.find(a => a.id === data.id);
          if (found) {
            setAgent(found as AgentData);
          } else {
            setError(t('detail.notFound'));
          }
        } else {
          setError(response.error || t('detail.fetchError'));
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchAgent();
  }, [data, t]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-[#39ff14] animate-pulse">
          $ {t('detail.loading')}
          <span className="cursor-blink">▋</span>
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const phaseColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    divergence: 'cyan',
    convergence: 'orange',
    planning: 'purple',
  };

  const roleColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    founder: 'green',
    vc: 'cyan',
    accelerator: 'orange',
    founder_friend: 'purple',
  };

  const personalityTraits = [
    { key: 'creativity', label: t('detail.creativity'), color: 'purple' as const },
    { key: 'analytical', label: t('detail.analytical'), color: 'cyan' as const },
    { key: 'risk_tolerance', label: t('detail.riskTolerance'), color: 'orange' as const },
    { key: 'collaboration', label: t('detail.collaboration'), color: 'green' as const },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="text-center">
        <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-[#39ff14]/20 to-[#00ffff]/20 border-2 border-[#39ff14] flex items-center justify-center">
          <span className="text-3xl font-bold text-[#39ff14]">
            {agent.name.charAt(0).toUpperCase()}
          </span>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{agent.name}</h3>
        {agent.handle && (
          <div className="text-sm text-[#00ffff]">@{agent.handle}</div>
        )}
        <div className="flex items-center justify-center gap-2 mt-2">
          <TerminalBadge variant={roleColors[agent.role] || 'green'}>
            {agent.role}
          </TerminalBadge>
          <TerminalBadge variant={phaseColors[agent.phase] || 'cyan'}>
            {agent.phase}
          </TerminalBadge>
        </div>
      </div>

      {/* Description */}
      {agent.description && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.agentDescription')}</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">{agent.description}</p>
        </div>
      )}

      {/* Personality Traits */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">{t('detail.personalityProfile')}</div>
        <div className="space-y-4">
          {personalityTraits.map((trait, idx) => (
            <motion.div
              key={trait.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <ScoreGauge
                value={agent.personality[trait.key as keyof typeof agent.personality]}
                maxValue={10}
                label={trait.label}
                color={trait.color}
              />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Role Perspective */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.rolePerspective')}</div>
        <div className="text-sm text-[#c0c0c0]">
          {t(`role.${agent.role}.perspective`)}
        </div>
      </div>

      {/* Personality Radar (ASCII style) */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">{t('detail.traitRadar')}</div>
        <div className="grid grid-cols-2 gap-4 text-center">
          {personalityTraits.map((trait) => {
            const value = agent.personality[trait.key as keyof typeof agent.personality];
            const bars = Math.round(value);
            return (
              <div key={trait.key} className="space-y-1">
                <div className="text-xs text-[#6b7280]">{trait.label}</div>
                <div className="text-[#39ff14] font-mono text-sm">
                  {'█'.repeat(bars)}
                  <span className="text-[#21262d]">{'░'.repeat(10 - bars)}</span>
                </div>
                <div className="text-xs text-[#c0c0c0]">{value.toFixed(1)}</div>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
