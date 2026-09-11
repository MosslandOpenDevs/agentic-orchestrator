'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { useModal } from '@/components/modals/useModal';
import { formatLocalDateTime } from '@/lib/date';
import type { Trend } from '@/lib/types';

interface TrendCardProps {
  trend: Trend;
  index: number;
  trendId?: string;
}

const categoryColors: Record<string, string> = {
  ai: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  crypto: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  defi: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  security: 'bg-red-500/20 text-red-400 border-red-500/30',
  dev: 'bg-green-500/20 text-green-400 border-green-500/30',
  finance: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  general: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
};

export function TrendCard({ trend, index, trendId }: TrendCardProps) {
  const { t, locale } = useI18n();
  const { openModal } = useModal();
  const [isExpanded, setIsExpanded] = useState(false);
  const categoryStyle = categoryColors[trend.category] || categoryColors.general;

  const handleViewDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    openModal('trend', {
      id: trendId || `trend-${index}`,
      title: trend.title,
      name: trend.title,
      score: trend.score,
      category: trend.category,
      signal_count: trend.articles,
      description: trend.summary,
      keywords: trend.ideaSeeds,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-lg border border-zinc-800 bg-zinc-900/50 transition-colors hover:border-zinc-700"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`rounded border px-2 py-0.5 text-xs ${categoryStyle}`}>
                {trend.category.toUpperCase()}
              </span>
              <span className="font-mono text-xs text-zinc-500">
                {trend.articles} {t('trends.articles')}
              </span>
              {trend.analyzedAt && (
                <span className="font-mono text-xs text-zinc-600">
                  • {formatLocalDateTime(trend.analyzedAt, locale)}
                </span>
              )}
            </div>
            <h4 className="mt-2 font-medium text-white">{trend.title}</h4>
            {!isExpanded && trend.summary && (
              <p className="mt-2 text-sm text-zinc-400 line-clamp-2">{trend.summary}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="text-right">
              <div className="font-mono text-2xl font-bold text-white">{trend.score.toFixed(1)}</div>
              <span className="text-xs text-zinc-500">{t('trends.score')}</span>
            </div>
            <motion.span
              animate={{ rotate: isExpanded ? 180 : 0 }}
              className="text-zinc-500"
            >
              ▼
            </motion.span>
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t border-zinc-800 p-4">
              {trend.summary && (
                <div className="mb-4">
                  <h5 className="mb-2 text-xs font-medium text-zinc-500">Summary</h5>
                  <p className="text-sm text-zinc-300">{trend.summary}</p>
                </div>
              )}

              {trend.ideaSeeds && trend.ideaSeeds.length > 0 && (
                <div className="mb-4">
                  <h5 className="mb-2 text-xs font-medium text-zinc-500">{t('trends.ideaSeeds')}</h5>
                  <div className="flex flex-wrap gap-2">
                    {trend.ideaSeeds.map((seed, i) => (
                      <span
                        key={i}
                        className="rounded bg-zinc-800 px-2 py-1 text-xs text-zinc-300"
                      >
                        {seed}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleViewDetails}
                  className="inline-flex items-center gap-1 rounded bg-purple-500/20 border border-purple-500/30 px-3 py-1.5 text-xs text-purple-400 transition-colors hover:bg-purple-500/30"
                >
                  <span>🔍</span>
                  {t('transparency.viewDetails')}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
