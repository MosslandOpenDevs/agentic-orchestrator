'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';

interface ScoreDimension {
  key: string;
  label: string;
  value: number;
  weight: number;
}

interface ScoreBreakdownProps {
  score: number;
  dimensions?: ScoreDimension[];
  consensus?: number;
  confidence?: 'low' | 'medium' | 'high';
  showDetails?: boolean;
}

// This component used to invent the per-dimension scores it displays --
// `score + Math.random() * 1.5` per bar, re-rolled on every render, printed to
// one decimal place next to the real weights. On a page titled "transparency"
// that is the one thing it must not do. The backend records a single overall
// score today, so when a caller has no real breakdown to pass we say so.

export function ScoreBreakdown({
  score,
  dimensions,
  consensus,
  // No default. A default here does not mean "unspecified", it means the
  // component prints `Confidence: MED (±0.8)` for every idea whose caller
  // passes nothing -- a fabricated error bar, rendered directly under the
  // sentence saying no breakdown was recorded.
  confidence,
  showDetails = true,
}: ScoreBreakdownProps) {
  const { t } = useI18n();

  const displayDimensions = dimensions;

  const confidenceRange =
    confidence === 'high' ? 0.3 : confidence === 'medium' ? 0.8 : 1.5;

  const getBarColor = (value: number) => {
    if (value >= 8) return 'bg-[#39ff14]';
    if (value >= 6) return 'bg-[#00ffff]';
    if (value >= 4) return 'bg-[#ff6b35]';
    return 'bg-[#ff5555]';
  };

  const getConfidenceLabel = () => {
    switch (confidence) {
      case 'high': return t('scoreBreakdown.highConfidence');
      case 'medium': return t('scoreBreakdown.mediumConfidence');
      case 'low': return t('scoreBreakdown.lowConfidence');
    }
  };

  const getConfidenceColor = () => {
    switch (confidence) {
      case 'high': return 'text-[#39ff14]';
      case 'medium': return 'text-[#ff6b35]';
      case 'low': return 'text-[#ff5555]';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with total score */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#8b949e] uppercase tracking-wider">
          {t('scoreBreakdown.title')}
        </span>
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="text-2xl font-bold text-[#39ff14]"
        >
          {score.toFixed(1)}
        </motion.span>
      </div>

      {/* Dimension bars, only when a real breakdown was recorded */}
      {showDetails && !displayDimensions && (
        <p className="text-xs text-[#8b949e] leading-relaxed">
          {t('scoreBreakdown.noBreakdown')}
        </p>
      )}
      {showDetails && displayDimensions && (
        <div className="space-y-3">
          {displayDimensions.map((dim, idx) => (
            <motion.div
              key={dim.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-[#c0c0c0]">{t(`scoreBreakdown.${dim.label}`)}</span>
                <span className="text-[#8b949e]">
                  {dim.value.toFixed(1)} <span className="text-[#3b3b3b]">({dim.weight}%)</span>
                </span>
              </div>
              <div className="h-2 bg-[#21262d] rounded-sm overflow-hidden">
                <motion.div
                  className={`h-full ${getBarColor(dim.value)} shadow-[0_0_6px_rgba(57,255,20,0.3)]`}
                  initial={{ width: 0 }}
                  animate={{ width: `${(dim.value / 10) * 100}%` }}
                  transition={{ duration: 0.6, delay: idx * 0.1 }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Footer stats, only for figures the caller actually has */}
      {(consensus !== undefined || confidence !== undefined) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="pt-3 border-t border-[#21262d] flex items-center justify-between text-xs"
        >
          {consensus !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-[#8b949e]">{t('scoreBreakdown.consensus')}:</span>
              <span className="text-[#00ffff] font-bold">{consensus}%</span>
            </div>
          )}
          {confidence !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-[#8b949e]">{t('scoreBreakdown.confidence')}:</span>
              <span className={`font-bold ${getConfidenceColor()}`}>
                {getConfidenceLabel()}{' '}
                <span className="text-[#3b3b3b]">(±{confidenceRange.toFixed(1)})</span>
              </span>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

// Compact version for cards. Renders nothing without a real breakdown --
// the sparkline of invented bars it used to draw was pure decoration that read
// as data.
export function ScoreBreakdownCompact({
  dimensions,
}: {
  dimensions?: ScoreDimension[];
}) {
  const { t } = useI18n();
  if (!dimensions) return null;

  return (
    <div className="flex items-center gap-1">
      {dimensions.map((dim, idx) => (
        <motion.div
          key={dim.key}
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ delay: idx * 0.05 }}
          className="relative group"
          title={`${t(`scoreBreakdown.${dim.label}`)}: ${dim.value.toFixed(1)}`}
        >
          <div className="w-1.5 h-6 bg-[#21262d] rounded-sm overflow-hidden flex flex-col-reverse">
            <div
              className={`transition-all ${
                dim.value >= 8 ? 'bg-[#39ff14]' :
                dim.value >= 6 ? 'bg-[#00ffff]' :
                dim.value >= 4 ? 'bg-[#ff6b35]' : 'bg-[#ff5555]'
              }`}
              style={{ height: `${(dim.value / 10) * 100}%` }}
            />
          </div>
        </motion.div>
      ))}
    </div>
  );
}
