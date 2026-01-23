'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { useModal } from '@/components/modals/useModal';
import type { Idea } from '@/lib/types';

interface IdeaCardProps {
  idea: Idea;
  index: number;
  ideaId?: string;
}

const statusStyles: Record<string, { bg: string; text: string; label: string }> = {
  backlog: { bg: 'bg-zinc-500/20', text: 'text-zinc-400', label: 'Backlog' },
  planned: { bg: 'bg-purple-500/20', text: 'text-purple-400', label: 'Planned' },
  'in-dev': { bg: 'bg-green-500/20', text: 'text-green-400', label: 'In Dev' },
  done: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Done' },
};

export function IdeaCard({ idea, index, ideaId }: IdeaCardProps) {
  const { t } = useI18n();
  const { openModal } = useModal();
  const style = statusStyles[idea.status] || statusStyles.backlog;

  const handleViewDetails = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openModal('idea', {
      id: ideaId || String(idea.id),
      title: idea.title,
    });
  };

  const CardContent = (
    <>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-zinc-600">#{idea.id}</span>
            <span className={`rounded px-2 py-0.5 text-xs ${style.bg} ${style.text}`}>
              {style.label}
            </span>
            {idea.source === 'trend' && (
              <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs text-blue-400">
                Trend
              </span>
            )}
          </div>
          <h4 className="mt-2 font-medium text-white">{idea.title}</h4>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="font-mono text-xs text-zinc-500">{idea.created}</div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleViewDetails}
              className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
              title={t('transparency.viewDetails')}
            >
              🔍
            </button>
            {idea.issueUrl && (
              <span className="text-xs text-zinc-600 group-hover:text-green-400 transition-colors">
                GitHub →
              </span>
            )}
          </div>
        </div>
      </div>
    </>
  );

  if (idea.issueUrl) {
    return (
      <motion.a
        href={idea.issueUrl}
        target="_blank"
        rel="noopener noreferrer"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ y: -2 }}
        className="group block rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 transition-colors hover:border-green-500/50 hover:bg-zinc-900"
      >
        {CardContent}
      </motion.a>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
    >
      {CardContent}
    </motion.div>
  );
}
