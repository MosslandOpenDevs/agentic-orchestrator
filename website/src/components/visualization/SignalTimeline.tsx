'use client';


import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';

interface TimeSlot {
  label: string;
  count: number;
  hour?: number;
}

interface SignalTimelineProps {
  data: TimeSlot[];
  totalSignals?: number;
  period?: '24h' | '7d';
  showDetails?: boolean;
}

// The two "generate mock data" functions that used to live here built a
// plausible 24-hour or 7-day chart out of Math.random() and an assumption
// about work hours, and were used whenever `data` was absent. A chart is a
// measurement; an outage that renders as a normal-looking histogram is worse
// than one that renders as nothing. `data` is required instead -- the only
// caller has always passed it, and its own loading state is the honest
// placeholder.

export function SignalTimeline({
  data,
  totalSignals,
  period = '24h',
  showDetails = true,
}: SignalTimelineProps) {
  const { t } = useI18n();

  const timelineData = data;

  const maxCount = Math.max(...timelineData.map(d => d.count), 1);
  const total = timelineData.reduce((sum, d) => sum + d.count, 0);
  const average = Math.round(total / timelineData.length);

  // Find peak time
  const peakSlot = timelineData.reduce((max, d) => d.count > max.count ? d : max, timelineData[0]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#8b949e] uppercase tracking-wider">
          {t('signalTimeline.title')}
        </span>
        <span className="text-xs text-[#c0c0c0]">
          {period === '24h' ? t('signalTimeline.last24h') : t('signalTimeline.last7d')}
        </span>
      </div>

      {/* Chart */}
      {showDetails && (
        <div className="relative">
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 bottom-6 w-8 flex flex-col justify-between text-[8px] text-[#8b949e]">
            <span>{maxCount}</span>
            <span>{Math.round(maxCount / 2)}</span>
            <span>0</span>
          </div>

          {/* Chart area */}
          <div className="ml-10">
            {/* Bars */}
            <div className="flex items-end gap-0.5 h-32">
              {timelineData.map((slot, idx) => {
                const height = (slot.count / maxCount) * 100;
                const isCurrentOrRecent = idx >= timelineData.length - 2;

                return (
                  <motion.div
                    key={slot.label}
                    initial={{ scaleY: 0 }}
                    animate={{ scaleY: 1 }}
                    transition={{ delay: idx * 0.02, duration: 0.3 }}
                    className="flex-1 flex flex-col items-center group"
                    style={{ originY: 1 }}
                  >
                    {/* Tooltip */}
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-[#21262d] border border-[#39ff14]/30 rounded px-2 py-1 text-[10px] text-[#c0c0c0] whitespace-nowrap z-10">
                      {slot.label}: {slot.count} {t('signalTimeline.signals')}
                    </div>

                    {/* Bar */}
                    <div
                      className={`w-full rounded-t-sm transition-colors ${
                        isCurrentOrRecent
                          ? 'bg-[#39ff14]'
                          : slot.count === peakSlot.count
                            ? 'bg-[#00ffff]'
                            : 'bg-[#39ff14]/50'
                      } group-hover:bg-[#39ff14]`}
                      style={{ height: `${Math.max(height, 2)}%` }}
                    />
                  </motion.div>
                );
              })}
            </div>

            {/* X-axis labels */}
            <div className="flex justify-between mt-1 text-[8px] text-[#8b949e] overflow-hidden">
              {timelineData
                .filter((_, idx) => {
                  // Show every 4th label for 24h, every label for 7d
                  if (period === '24h') return idx % 4 === 0 || idx === timelineData.length - 1;
                  return true;
                })
                .map(slot => (
                  <span key={slot.label} className="truncate">
                    {slot.label}
                  </span>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-3 gap-4 pt-3 border-t border-[#21262d]"
      >
        <div className="text-center">
          <div className="text-lg font-bold text-[#39ff14]">{totalSignals || total}</div>
          <div className="text-[10px] text-[#8b949e]">{t('signalTimeline.total')}</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#00ffff]">{average}</div>
          <div className="text-[10px] text-[#8b949e]">
            {t('signalTimeline.avg')}/{period === '24h' ? t('signalTimeline.hour') : t('signalTimeline.day')}
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-[#bd93f9]">{peakSlot.label}</div>
          <div className="text-[10px] text-[#8b949e]">
            {t('signalTimeline.peak')} ({peakSlot.count})
          </div>
        </div>
      </motion.div>

      {/* Legend */}
      <div className="flex justify-center gap-4 text-[10px]">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-sm bg-[#39ff14]" />
          <span className="text-[#8b949e]">{t('signalTimeline.recent')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-sm bg-[#00ffff]" />
          <span className="text-[#8b949e]">{t('signalTimeline.peakTime')}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-sm bg-[#39ff14]/50" />
          <span className="text-[#8b949e]">{t('signalTimeline.normal')}</span>
        </div>
      </div>
    </div>
  );
}

// Mini version for embedding in cards
export function SignalTimelineMini({ data, period = '24h' }: { data: TimeSlot[]; period?: '24h' | '7d' }) {
  const timelineData = data;

  const maxCount = Math.max(...timelineData.map(d => d.count), 1);

  // Downsample for mini view
  const sampledData = period === '24h'
    ? timelineData.filter((_, idx) => idx % 3 === 0)
    : timelineData;

  return (
    <div className="flex items-end gap-0.5 h-6">
      {sampledData.map((slot, idx) => {
        const height = (slot.count / maxCount) * 100;
        const isRecent = idx >= sampledData.length - 2;

        return (
          <motion.div
            key={slot.label}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: idx * 0.03 }}
            className={`w-1 rounded-t-sm ${
              isRecent ? 'bg-[#39ff14]' : 'bg-[#39ff14]/40'
            }`}
            style={{ height: `${Math.max(height, 10)}%` }}
          />
        );
      })}
    </div>
  );
}
