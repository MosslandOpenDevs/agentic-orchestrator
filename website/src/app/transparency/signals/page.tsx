'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type ApiSignal } from '@/lib/api';
import { useModal } from '@/components/modals/useModal';
import { TerminalWindow, TerminalBadge } from '@/components/TerminalWindow';

export default function SignalsPage() {
  const { t } = useI18n();
  const { openModal } = useModal();
  const [signals, setSignals] = useState<ApiSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<{ source?: string; category?: string; minScore?: number }>({});
  const [sources, setSources] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    async function fetchSignals() {
      setLoading(true);
      const response = await ApiClient.getSignals({
        limit: 100,
        source: filter.source,
        category: filter.category,
        min_score: filter.minScore,
      });

      if (response.data) {
        setSignals(response.data.signals);

        // Extract unique sources and categories
        const uniqueSources = [...new Set(response.data.signals.map(s => s.source))];
        const uniqueCategories = [...new Set(response.data.signals.map(s => s.category))];
        setSources(uniqueSources);
        setCategories(uniqueCategories);
      }
      setLoading(false);
    }

    fetchSignals();
  }, [filter]);

  const handleSignalClick = (signal: ApiSignal) => {
    openModal('signal', {
      ...signal,
      title: signal.title,
    });
  };

  const scoreColors = (score: number) => {
    if (score >= 8) return 'text-[#39ff14]';
    if (score >= 6) return 'text-[#00ffff]';
    if (score >= 4) return 'text-[#f1fa8c]';
    return 'text-[#ff6b35]';
  };

  return (
    <div className="min-h-screen pt-14 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-bold text-[#00ffff] mb-2">
            📡 {t('signals.title')}
          </h1>
          <p className="text-sm text-[#6b7280]">
            {t('signals.subtitle')}
          </p>
        </motion.div>

        {/* Filters */}
        <TerminalWindow title="FILTERS" className="mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Source Filter */}
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('signals.source')}</label>
              <select
                value={filter.source || ''}
                onChange={(e) => setFilter({ ...filter, source: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('signals.allSources')}</option>
                {sources.map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('signals.category')}</label>
              <select
                value={filter.category || ''}
                onChange={(e) => setFilter({ ...filter, category: e.target.value || undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('signals.allCategories')}</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            {/* Min Score Filter */}
            <div>
              <label className="text-xs text-[#6b7280] block mb-1">{t('signals.minScore')}</label>
              <select
                value={filter.minScore || ''}
                onChange={(e) => setFilter({ ...filter, minScore: e.target.value ? Number(e.target.value) : undefined })}
                className="input-cli text-sm"
              >
                <option value="">{t('signals.anyScore')}</option>
                <option value="8">8+ ({t('signals.high')})</option>
                <option value="6">6+ ({t('signals.medium')})</option>
                <option value="4">4+ ({t('signals.low')})</option>
              </select>
            </div>
          </div>
        </TerminalWindow>

        {/* Signals Grid */}
        <TerminalWindow title={`SIGNALS (${signals.length})`}>
          {loading ? (
            <div className="text-center py-12">
              <div className="text-[#00ffff] animate-pulse">
                $ {t('detail.loading')}
                <span className="cursor-blink">▋</span>
              </div>
            </div>
          ) : signals.length === 0 ? (
            <div className="text-center py-12 text-[#6b7280]">
              {t('signals.noSignals')}
            </div>
          ) : (
            <div className="space-y-3">
              {signals.map((signal, idx) => (
                <motion.div
                  key={signal.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  onClick={() => handleSignalClick(signal)}
                  className="card-cli p-4 cursor-pointer hover:border-[#00ffff] transition-colors"
                >
                  <div className="flex items-start gap-4">
                    {/* Score */}
                    <div className={`text-xl font-bold ${scoreColors(signal.score)} w-12 text-center`}>
                      {signal.score.toFixed(1)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <TerminalBadge variant="cyan">{signal.source}</TerminalBadge>
                        <TerminalBadge variant="purple">{signal.category}</TerminalBadge>
                        {signal.sentiment && (
                          <TerminalBadge
                            variant={signal.sentiment === 'positive' ? 'green' : signal.sentiment === 'negative' ? 'red' : 'cyan'}
                          >
                            {signal.sentiment}
                          </TerminalBadge>
                        )}
                      </div>
                      <h3 className="text-sm font-medium text-[#c0c0c0] truncate">
                        {signal.title}
                      </h3>
                      {signal.summary && (
                        <p className="text-xs text-[#6b7280] mt-1 line-clamp-2">
                          {signal.summary}
                        </p>
                      )}
                      {signal.topics && signal.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {signal.topics.slice(0, 3).map(topic => (
                            <span key={topic} className="text-[10px] text-[#bd93f9]">
                              #{topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Arrow */}
                    <div className="text-[#21262d]">→</div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </TerminalWindow>
      </div>
    </div>
  );
}
