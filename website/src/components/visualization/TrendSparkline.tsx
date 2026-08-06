'use client';

import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { useI18n } from '@/lib/i18n';

interface SignalHistoryItem {
  day: string;
  count: number;
}

interface TrendSparklineProps {
  signalHistory?: SignalHistoryItem[];
  momentum?: number; // Percentage change (e.g., +15, -10)
  velocity?: number; // Signals per day
  showDetails?: boolean;
}

// A simulated 7-day history used to be invented here from the current
// count plus Math.random(), and rendered under the heading "Trend
// Momentum" complete with derived momentum and velocity figures. None of
// it came from the backend. Until a real history endpoint exists, this
// component renders only what it was actually given.

export function TrendSparkline({
  signalHistory,
  momentum,
  velocity,
  showDetails = true,
}: TrendSparklineProps) {
  const { t } = useI18n();

  const history = useMemo(() => signalHistory ?? [], [signalHistory]);

  // Calculate momentum if not provided
  const calculatedMomentum = useMemo(() => {
    if (momentum !== undefined) return momentum;
    if (history.length < 2) return 0;

    const recent = history.slice(-3).reduce((sum, h) => sum + h.count, 0);
    const earlier = history.slice(0, 3).reduce((sum, h) => sum + h.count, 0);

    if (earlier === 0) return 100;
    return Math.round(((recent - earlier) / earlier) * 100);
  }, [momentum, history]);

  // Calculate velocity if not provided
  const calculatedVelocity = useMemo(() => {
    if (velocity !== undefined) return velocity;
    const total = history.reduce((sum, h) => sum + h.count, 0);
    return +(total / history.length).toFixed(1);
  }, [velocity, history]);

  const maxCount = history.length ? Math.max(...history.map(h => h.count)) : 0;

  const getMomentumColor = () => {
    if (calculatedMomentum >= 10) return 'text-[#39ff14]';
    if (calculatedMomentum >= 0) return 'text-[#00ffff]';
    if (calculatedMomentum >= -10) return 'text-[#ff6b35]';
    return 'text-[#ff5555]';
  };

  const getMomentumIcon = () => {
    if (calculatedMomentum >= 10) return '↑';
    if (calculatedMomentum >= 0) return '→';
    return '↓';
  };

  if (history.length === 0) {
    return (
      <div className="space-y-2">
        <span className="text-xs text-[#8b949e] uppercase tracking-wider">
          {t('trendSparkline.momentum')}
        </span>
        <p className="text-xs text-[#8b949e]">{t('trendSparkline.noHistory')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header with momentum */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#8b949e] uppercase tracking-wider">
          {t('trendSparkline.momentum')}
        </span>
        <motion.div
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex items-center gap-1 font-bold ${getMomentumColor()}`}
        >
          <span className="text-lg">{getMomentumIcon()}</span>
          <span>
            {calculatedMomentum >= 0 ? '+' : ''}{calculatedMomentum}%
          </span>
        </motion.div>
      </div>

      {/* Sparkline chart */}
      {showDetails && (
        <div className="space-y-1">
          <div className="text-xs text-[#8b949e] mb-2">
            {t('trendSparkline.last7Days')}:
          </div>
          <div className="space-y-1">
            {history.map((item, idx) => (
              <motion.div
                key={item.day}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-2 text-xs"
              >
                <span className="w-8 text-[#8b949e] font-mono">{item.day}</span>
                <div className="flex-1 h-3 bg-[#21262d] rounded-sm overflow-hidden">
                  <motion.div
                    className={`h-full ${
                      idx === history.length - 1 ? 'bg-[#39ff14]' : 'bg-[#39ff14]/60'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: maxCount > 0 ? `${(item.count / maxCount) * 100}%` : '0%' }}
                    transition={{ duration: 0.4, delay: idx * 0.05 }}
                  />
                </div>
                <span className={`w-8 text-right font-mono ${
                  idx === history.length - 1 ? 'text-[#39ff14]' : 'text-[#8b949e]'
                }`}>
                  {item.count}
                </span>
                {idx === history.length - 1 && (
                  <span className="text-[#39ff14]">←</span>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Footer stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="pt-2 border-t border-[#21262d] text-xs text-[#8b949e]"
      >
        {t('trendSparkline.velocity')}: <span className="text-[#00ffff] font-bold">+{calculatedVelocity}</span> {t('trendSparkline.signalsPerDay')}
      </motion.div>
    </div>
  );
}

// Compact sparkline for cards
export function TrendSparklineCompact({
  signalHistory,
  momentum,
}: {
  signalHistory?: SignalHistoryItem[];
  momentum?: number;
}) {
  const history = useMemo(() => signalHistory ?? [], [signalHistory]);

  const calculatedMomentum = useMemo(() => {
    if (momentum !== undefined) return momentum;
    if (history.length < 2) return 0;

    const recent = history.slice(-3).reduce((sum, h) => sum + h.count, 0);
    const earlier = history.slice(0, 3).reduce((sum, h) => sum + h.count, 0);

    if (earlier === 0) return 100;
    return Math.round(((recent - earlier) / earlier) * 100);
  }, [momentum, history]);

  const maxCount = history.length ? Math.max(...history.map(h => h.count)) : 0;

  return (
    <div className="flex items-center gap-2">
      {/* Mini sparkline bars */}
      <div className="flex items-end gap-0.5 h-4">
        {history.map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: idx * 0.03 }}
            className={`w-1 rounded-t-sm ${
              idx === history.length - 1 ? 'bg-[#39ff14]' : 'bg-[#39ff14]/40'
            }`}
            style={{
              height: maxCount > 0 ? `${Math.max(10, (item.count / maxCount) * 100)}%` : '10%',
            }}
          />
        ))}
      </div>

      {/* Momentum indicator */}
      <span className={`text-xs font-bold ${
        calculatedMomentum >= 10 ? 'text-[#39ff14]' :
        calculatedMomentum >= 0 ? 'text-[#00ffff]' :
        calculatedMomentum >= -10 ? 'text-[#ff6b35]' : 'text-[#ff5555]'
      }`}>
        {calculatedMomentum >= 0 ? '↑' : '↓'}
        {Math.abs(calculatedMomentum)}%
      </span>
    </div>
  );
}
