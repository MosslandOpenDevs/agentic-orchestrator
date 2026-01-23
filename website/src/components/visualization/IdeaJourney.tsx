'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ApiIdea, ApiDebate, ApiPlan } from '@/lib/api';

interface IdeaJourneyProps {
  idea: ApiIdea;
  debates: ApiDebate[];
  plans: ApiPlan[];
}

interface JourneyStep {
  type: 'signal' | 'trend' | 'idea' | 'debate' | 'plan';
  label: string;
  status: 'completed' | 'active' | 'pending';
  timestamp?: string;
  details?: string;
}

export function IdeaJourney({ idea, debates, plans }: IdeaJourneyProps) {
  const { t } = useI18n();

  // Build journey steps from idea lifecycle
  const steps: JourneyStep[] = [
    {
      type: 'signal',
      label: t('journey.signalCollected'),
      status: 'completed',
      details: idea.source_type,
    },
    {
      type: 'trend',
      label: t('journey.trendIdentified'),
      status: 'completed',
    },
    {
      type: 'idea',
      label: t('journey.ideaGenerated'),
      status: 'completed',
      timestamp: idea.created_at || undefined,
      details: `Score: ${idea.score.toFixed(1)}`,
    },
  ];

  // Add debate steps
  debates.forEach((debate, idx) => {
    steps.push({
      type: 'debate',
      label: `${t('journey.debateRound')} ${idx + 1}`,
      status: debate.status === 'completed' ? 'completed' : 'active',
      timestamp: debate.completed_at || debate.started_at || undefined,
      details: `${debate.phase} - ${debate.message_count || 0} ${t('detail.messages')}`,
    });
  });

  // Add plan steps
  plans.forEach((plan) => {
    steps.push({
      type: 'plan',
      label: `${t('journey.planVersion')} ${plan.version}`,
      status: plan.status === 'approved' ? 'completed' : plan.status === 'draft' ? 'active' : 'pending',
      timestamp: plan.created_at || undefined,
      details: plan.status,
    });
  });

  // Add final status
  if (idea.status === 'in-development') {
    steps.push({
      type: 'plan',
      label: t('journey.inDevelopment'),
      status: 'active',
    });
  } else if (idea.status === 'done') {
    steps.push({
      type: 'plan',
      label: t('journey.completed'),
      status: 'completed',
    });
  }

  const typeColors: Record<string, { bg: string; border: string; text: string }> = {
    signal: { bg: 'bg-[#00ffff]/10', border: 'border-[#00ffff]', text: 'text-[#00ffff]' },
    trend: { bg: 'bg-[#bd93f9]/10', border: 'border-[#bd93f9]', text: 'text-[#bd93f9]' },
    idea: { bg: 'bg-[#39ff14]/10', border: 'border-[#39ff14]', text: 'text-[#39ff14]' },
    debate: { bg: 'bg-[#ff6b35]/10', border: 'border-[#ff6b35]', text: 'text-[#ff6b35]' },
    plan: { bg: 'bg-[#00ffff]/10', border: 'border-[#00ffff]', text: 'text-[#00ffff]' },
  };

  const statusStyles = {
    completed: 'opacity-100',
    active: 'opacity-100 animate-pulse',
    pending: 'opacity-50',
  };

  return (
    <div className="idea-journey relative">
      {/* Horizontal flow on desktop, vertical on mobile */}
      <div className="flex flex-col md:flex-row gap-2 md:gap-0">
        {steps.map((step, idx) => {
          const colors = typeColors[step.type];
          const statusStyle = statusStyles[step.status];

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className={`flex items-center ${statusStyle}`}
            >
              {/* Step node */}
              <div className={`
                relative flex-shrink-0 w-full md:w-auto
                ${colors.bg} ${colors.border} border rounded p-2
                ${step.status === 'active' ? `ring-2 ring-offset-2 ring-offset-[#0d1117] ${colors.border.replace('border-', 'ring-')}` : ''}
              `}
              >
                <div className="flex items-center gap-2">
                  {/* Type icon */}
                  <div className={`w-6 h-6 rounded-full ${colors.bg} ${colors.border} border flex items-center justify-center`}>
                    <span className={`text-xs ${colors.text}`}>
                      {step.type === 'signal' && '📡'}
                      {step.type === 'trend' && '📈'}
                      {step.type === 'idea' && '💡'}
                      {step.type === 'debate' && '💬'}
                      {step.type === 'plan' && '📋'}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className={`text-xs font-medium ${colors.text} truncate`}>
                      {step.label}
                    </div>
                    {step.details && (
                      <div className="text-[10px] text-[#6b7280] truncate">
                        {step.details}
                      </div>
                    )}
                  </div>

                  {/* Status indicator */}
                  {step.status === 'completed' && (
                    <span className="text-[#39ff14] text-xs">✓</span>
                  )}
                  {step.status === 'active' && (
                    <span className="w-2 h-2 rounded-full bg-[#39ff14] animate-pulse" />
                  )}
                </div>
              </div>

              {/* Connector arrow (hidden on last item) */}
              {idx < steps.length - 1 && (
                <div className="hidden md:flex items-center px-1">
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.1 + 0.05 }}
                    className="text-[#21262d] text-xs"
                  >
                    →
                  </motion.span>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-[10px]">
        {Object.entries(typeColors).map(([type, colors]) => (
          <div key={type} className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${colors.bg} ${colors.border} border`} />
            <span className="text-[#6b7280] uppercase">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
