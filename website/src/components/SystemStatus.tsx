'use client';

import { motion } from 'framer-motion';
import { formatDistanceToNow, parseISO, format, isValid, isPast } from 'date-fns';
import { ko, enUS } from 'date-fns/locale';
import { useI18n } from '@/lib/i18n';
import type { SystemHealth } from '@/lib/types';

interface SystemStatusProps {
  lastRun?: string;
  nextRun?: string;
  /** What /status reported. The banner used to read SYSTEM ONLINE with a
   *  green dot no matter what -- including while the API was unreachable. */
  status?: SystemHealth;
}

const STATUS_PRESENTATION: Record<SystemHealth, { dot: string; text: string; label: string }> = {
  operational: { dot: 'online', text: '#39ff14', label: 'SYSTEM ONLINE' },
  degraded: { dot: 'pending', text: '#ff6b35', label: 'SYSTEM DEGRADED' },
  unknown: { dot: 'unknown', text: '#8b949e', label: 'STATUS UNKNOWN' },
};

export function SystemStatus({ lastRun, nextRun, status = 'unknown' }: SystemStatusProps) {
  const { locale } = useI18n();
  const dateLocale = locale === 'ko' ? ko : enUS;
  const presentation = STATUS_PRESENTATION[status];
  const lastRunDate = lastRun ? parseISO(lastRun) : null;
  const nextRunDate = nextRun ? parseISO(nextRun) : null;
  // A "next run" in the past (stale data) should not render as "6 months ago".
  const nextRunPending = !nextRunDate || !isValid(nextRunDate) || isPast(nextRunDate);
  const nextRunLabel = nextRunPending
    ? locale === 'ko'
      ? '대기 중'
      : 'pending'
    : formatDistanceToNow(nextRunDate!, { addSuffix: true, locale: dateLocale });

  return (
    <div className="card-cli p-4">
      <div className="flex flex-wrap items-center gap-4 md:gap-8">
        {/* System Status */}
        <div className="flex items-center gap-3">
          <motion.div
            className={`status-dot ${presentation.dot}`}
            animate={{
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
          <div>
            <span
              className="text-xs font-bold tracking-wider"
              style={{ color: presentation.text }}
            >
              {presentation.label}
            </span>
          </div>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Last Run */}
        <div className="flex items-center gap-2">
          <span className="text-[#8b949e] text-xs">last_run:</span>
          <span className="text-[#c0c0c0] text-xs" suppressHydrationWarning>
            {lastRunDate && isValid(lastRunDate)
              ? formatDistanceToNow(lastRunDate, { addSuffix: true, locale: dateLocale })
              : '--'}
          </span>
          <span className="text-[#8b949e] text-[10px]" suppressHydrationWarning>
            ({lastRunDate && isValid(lastRunDate) ? format(lastRunDate, 'HH:mm:ss') : '--:--:--'})
          </span>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Next Run */}
        <div className="flex items-center gap-2">
          <span className="text-[#8b949e] text-xs">next_run:</span>
          <span className="text-[#00ffff] text-xs" suppressHydrationWarning>
            {nextRunLabel}
          </span>
        </div>

        <div className="h-4 w-px bg-[#21262d] hidden md:block" />

        {/* Uptime */}
        <div className="flex items-center gap-2">
          <span className="text-[#8b949e] text-xs">uptime:</span>
          <span className="text-[#f1fa8c] text-xs">99.9%</span>
        </div>
      </div>

      {/* Command line style */}
      <div className="mt-3 pt-3 border-t border-[#21262d]">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#00ffff]">$</span>
          <span className="text-[#c0c0c0]">moss-ao status --watch</span>
          <motion.span
            className="text-[#39ff14] cursor-blink"
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
          >
            ▋
          </motion.span>
        </div>
      </div>
    </div>
  );
}
