'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiIdea, type ApiDebate, type ApiPlan } from '@/lib/api';
import type { ModalData } from '../modals/ModalProvider';
import { IdeaJourney } from '../visualization/IdeaJourney';
import { ScoreGauge } from '../visualization/ScoreGauge';
import { TerminalBadge } from '../TerminalWindow';

interface IdeaDetailProps {
  data: ModalData;
}

interface IdeaWithDetails {
  idea: ApiIdea;
  debates: ApiDebate[];
  plans: ApiPlan[];
}

export function IdeaDetail({ data }: IdeaDetailProps) {
  const { t } = useI18n();
  const [ideaData, setIdeaData] = useState<IdeaWithDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchIdea() {
      setLoading(true);
      setError(null);

      try {
        const response = await ApiClient.getIdeaDetail(data.id);
        if (response.data) {
          setIdeaData(response.data);
        } else {
          setError(response.error || t('detail.fetchError'));
        }
      } catch {
        setError(t('detail.fetchError'));
      } finally {
        setLoading(false);
      }
    }

    fetchIdea();
  }, [data.id, t]);

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

  if (error || !ideaData) {
    return (
      <div className="text-center py-12">
        <div className="text-[#ff5555]">[ERROR] {error || t('detail.notFound')}</div>
      </div>
    );
  }

  const { idea, debates, plans } = ideaData;

  const statusColors: Record<string, 'green' | 'cyan' | 'orange' | 'purple'> = {
    backlog: 'cyan',
    planned: 'purple',
    'in-development': 'orange',
    done: 'green',
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TerminalBadge variant={statusColors[idea.status] || 'cyan'}>
            {idea.status}
          </TerminalBadge>
          <TerminalBadge variant="purple">{idea.source_type}</TerminalBadge>
        </div>
        <h3 className="text-lg font-bold text-[#c0c0c0]">{idea.title}</h3>
      </div>

      {/* Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.ideaScore')}</div>
          <ScoreGauge value={idea.score} maxValue={10} label={t('detail.potential')} color="green" />
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.debatesCount')}</div>
          <div className="text-3xl font-bold text-[#ff6b35]">{debates.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.rounds')}</div>
        </div>

        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.plansCount')}</div>
          <div className="text-3xl font-bold text-[#00ffff]">{plans.length}</div>
          <div className="text-xs text-[#6b7280]">{t('detail.versions')}</div>
        </div>
      </div>

      {/* Summary */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.summary')}</div>
        <p className="text-sm text-[#c0c0c0] leading-relaxed">{idea.summary}</p>
      </div>

      {/* Idea Journey Timeline */}
      <div className="card-cli p-4">
        <div className="text-xs text-[#6b7280] uppercase mb-4">{t('detail.ideaJourney')}</div>
        <IdeaJourney idea={idea} debates={debates} plans={plans} />
      </div>

      {/* Debates List */}
      {debates.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.debateHistory')}</div>
          <div className="space-y-2">
            {debates.map((debate, idx) => (
              <motion.div
                key={debate.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-3 p-2 bg-black/20 rounded hover:bg-black/30 transition-colors"
              >
                <span className="text-[#ff6b35] text-xs font-bold">
                  R{debate.round_number}
                </span>
                <span className="text-sm text-[#c0c0c0] flex-1">{debate.phase}</span>
                <TerminalBadge variant={debate.status === 'completed' ? 'green' : 'orange'}>
                  {debate.status}
                </TerminalBadge>
                <span className="text-xs text-[#6b7280]">
                  {debate.message_count || 0} {t('detail.messages')}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Plans List */}
      {plans.length > 0 && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.planVersions')}</div>
          <div className="space-y-2">
            {plans.map((plan, idx) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-3 p-2 bg-black/20 rounded hover:bg-black/30 transition-colors"
              >
                <span className="text-[#00ffff] text-xs font-bold">
                  v{plan.version}
                </span>
                <span className="text-sm text-[#c0c0c0] flex-1 truncate">{plan.title}</span>
                <TerminalBadge variant={plan.status === 'approved' ? 'green' : 'cyan'}>
                  {plan.status}
                </TerminalBadge>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Links */}
      {idea.github_issue_url && (
        <div className="card-cli p-4">
          <div className="text-xs text-[#6b7280] uppercase mb-2">{t('detail.links')}</div>
          <a
            href={idea.github_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[#00ffff] hover:underline text-sm"
          >
            <span>→</span>
            {t('detail.viewOnGitHub')}
          </a>
        </div>
      )}
    </motion.div>
  );
}
