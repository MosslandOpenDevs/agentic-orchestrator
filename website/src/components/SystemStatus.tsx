'use client';

import { motion } from 'framer-motion';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { ko, enUS } from 'date-fns/locale';
import { useI18n } from '@/lib/i18n';

interface SystemStatusProps {
  lastRun: string;
  nextRun: string;
}

export function SystemStatus({ lastRun, nextRun }: SystemStatusProps) {
  const { t, locale } = useI18n();
  const dateLocale = locale === 'ko' ? ko : enUS;
  const lastRunDate = parseISO(lastRun);
  const nextRunDate = parseISO(nextRun);

  return (
    <div className="flex items-center gap-6 text-sm">
      <motion.div
        className="flex items-center gap-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <motion.div
          className="h-2 w-2 rounded-full bg-green-500"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [1, 0.7, 1],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
        <span className="font-mono text-green-500">LIVE</span>
      </motion.div>
      
      <div className="text-zinc-500">
        {t('dashboard.lastRun')}{' '}
        <span className="text-zinc-300">
          {formatDistanceToNow(lastRunDate, { addSuffix: true, locale: dateLocale })}
        </span>
      </div>
      
      <div className="text-zinc-500">
        {t('dashboard.nextRun')}{' '}
        <span className="text-zinc-300">
          {formatDistanceToNow(nextRunDate, { addSuffix: true, locale: dateLocale })}
        </span>
      </div>
    </div>
  );
}
