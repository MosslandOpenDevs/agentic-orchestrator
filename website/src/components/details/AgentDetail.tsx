'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient } from '@/lib/api';
import type { ModalData } from '../modals/ModalProvider';
import { TerminalBadge } from '../TerminalWindow';

interface AgentDetailProps {
  data: ModalData;
}

/** The four personality axes the backend models, in the order it defines them
 *  (src/agentic_orchestrator/personas/personalities.py). */
export const PERSONALITY_AXES = ['thinking', 'decision', 'communication', 'action'] as const;
export type PersonalityAxis = (typeof PERSONALITY_AXES)[number];

interface AgentData {
  id: string;
  name: string;
  role: string;
  phase: string;
  /** The four binary axes the backend models (personas/personalities.py),
   *  e.g. { thinking: 'optimistic', decision: 'analytical', ... }.
   *  Optional: the agents page falls back to a static roster when /agents is
   *  unreachable, and that roster carries no per-axis values. Absent means
   *  "not reported", which is rendered as nothing rather than as a default. */
  personality?: Partial<Record<PersonalityAxis, string>>;
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

  const axisValues = PERSONALITY_AXES.map((axis) => ({
    axis,
    value: agent.personality?.[axis],
  })).filter((entry): entry is { axis: PersonalityAxis; value: string } => Boolean(entry.value));

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
          <div className="text-xs text-[#8b949e] uppercase mb-2">{t('detail.agentDescription')}</div>
          <p className="text-sm text-[#c0c0c0] leading-relaxed">{agent.description}</p>
        </div>
      )}

      {/* Personality. Four labelled choices, not four bars: the backend models
          each axis as one of two named styles, and the gauges that used to be
          here were fed `{creativity: 7, analytical: 7, risk_tolerance: 5,
          collaboration: 7}` written as literals in the agents page -- the same
          four numbers for every one of the 34 agents, under the heading
          "Personality Profile". Rendered only when the API reported them. */}
      {axisValues.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#8b949e] uppercase mb-4">
            {t('detail.personalityProfile')}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {axisValues.map(({ axis, value }, idx) => (
              <motion.div
                key={axis}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="rounded border border-[#21262d] p-2"
              >
                <div className="text-[10px] text-[#8b949e] uppercase">
                  {t(`detail.axis.${axis}`)}
                </div>
                <div className="text-sm text-[#39ff14]">{t(`detail.trait.${value}`)}</div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Role Perspective */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#8b949e] uppercase mb-2">{t('detail.rolePerspective')}</div>
        <div className="text-sm text-[#c0c0c0]">
          {t(`role.${agent.role}.perspective`)}
        </div>
      </div>

    </motion.div>
  );
}
