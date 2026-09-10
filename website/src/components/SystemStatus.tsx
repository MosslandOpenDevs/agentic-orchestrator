'use client';

import { motion } from 'framer-motion';
import { formatDistanceToNow, format, isValid } from 'date-fns';
import { parseUTCDate } from '@/lib/date';
import { ko, enUS } from 'date-fns/locale';
import { useI18n } from '@/lib/i18n';
import type { SystemHealth } from '@/lib/types';

interface SystemStatusProps {
  lastRun?: string;
  /** What /status reported. The banner used to read SYSTEM ONLINE with a
   *  green dot no matter what -- including while the API was unreachable. */
  status?: SystemHealth;
}

const STATUS_PRESENTATION: Record<SystemHealth, { dot: string; text: string; label: string }> = {
  operational: { dot: 'online', text: '#39ff14', label: 'SYSTEM ONLINE' },
  degraded: { dot: 'pending', text: '#ff6b35', label: 'SYSTEM DEGRADED' },
  unknown: { dot: 'unknown', text: '#8b949e', label: 'STATUS UNKNOWN' },
};

export function SystemStatus({ lastRun, status = 'unknown' }: SystemStatusProps) {
  const { locale } = useI18n();
  const dateLocale = locale === 'ko' ? ko : enUS;
  const presentation = STATUS_PRESENTATION[status];
  // parseUTCDate, not date-fns parseISO: a backend instant without a "Z" is
  // read by parseISO as the *viewer's* local wall clock, which in KST reports a
  // fresh run as nine hours old. The backend marks its instants now; this is
  // the second layer, and it is idempotent on an already-marked string.
  const lastRunDate = parseUTCDate(lastRun);

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

        {/* No next_run figure: the API does not report the scheduler's next
            tick, so this field was fed `undefined` on every render and could
            only ever print "pending". A permanent placeholder is not a status.

            No uptime figure: this read a hard-coded "99.9%" that nothing
            measured. The API reports no uptime, so the honest display is
            none at all. */}
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
