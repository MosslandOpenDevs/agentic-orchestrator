'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ActivityItem } from '@/lib/types';

interface ActivityFeedProps {
  activities: ActivityItem[];
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  const { t } = useI18n();

  const typeStyles: Record<string, { color: string; prefix: string }> = {
    trend: { color: 'text-blue-400', prefix: t('activity.trend') },
    idea: { color: 'text-yellow-400', prefix: t('activity.idea') },
    plan: { color: 'text-purple-400', prefix: t('activity.plan') },
    debate: { color: 'text-orange-400', prefix: t('activity.debate') },
    dev: { color: 'text-green-400', prefix: t('activity.dev') },
    system: { color: 'text-zinc-400', prefix: t('activity.system') },
  };

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-mono text-sm text-zinc-500">{t('activity.title')}</h3>
        <motion.div
          className="flex items-center gap-1.5"
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
          <span className="font-mono text-xs text-green-500">{t('activity.streaming')}</span>
        </motion.div>
      </div>

      <div className="h-64 overflow-y-auto font-mono text-sm">
        {activities.map((activity, index) => {
          const style = typeStyles[activity.type] || typeStyles.system;
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex gap-2 py-1"
            >
              <span className="text-zinc-600">[{activity.time}]</span>
              <span className={`${style.color} min-w-16`}>{style.prefix}</span>
              <span className="text-zinc-300">{activity.message}</span>
            </motion.div>
          );
        })}
        <motion.div
          className="flex items-center gap-2 py-1 text-zinc-600"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          <span>▋</span>
        </motion.div>
      </div>
    </div>
  );
}
