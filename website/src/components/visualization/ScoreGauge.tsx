'use client';

import { motion } from 'framer-motion';

interface ScoreGaugeProps {
  value: number;
  maxValue?: number;
  label?: string;
  color?: 'green' | 'cyan' | 'orange' | 'purple';
  showValue?: boolean;
}

export function ScoreGauge({
  value,
  maxValue = 10,
  label,
  color = 'green',
  showValue = true,
}: ScoreGaugeProps) {
  const percentage = Math.min((value / maxValue) * 100, 100);

  const colorClasses = {
    green: {
      bar: 'bg-[#39ff14]',
      text: 'text-[#39ff14]',
      glow: 'shadow-[0_0_10px_rgba(57,255,20,0.5)]',
    },
    cyan: {
      bar: 'bg-[#00ffff]',
      text: 'text-[#00ffff]',
      glow: 'shadow-[0_0_10px_rgba(0,255,255,0.5)]',
    },
    orange: {
      bar: 'bg-[#ff6b35]',
      text: 'text-[#ff6b35]',
      glow: 'shadow-[0_0_10px_rgba(255,107,53,0.5)]',
    },
    purple: {
      bar: 'bg-[#bd93f9]',
      text: 'text-[#bd93f9]',
      glow: 'shadow-[0_0_10px_rgba(189,147,249,0.5)]',
    },
  };

  const colors = colorClasses[color];

  return (
    <div className="space-y-2">
      {(label || showValue) && (
        <div className="flex justify-between items-center text-xs">
          {label && <span className="text-[#6b7280]">{label}</span>}
          {showValue && (
            <span className={colors.text}>
              {value.toFixed(1)}/{maxValue}
            </span>
          )}
        </div>
      )}

      {/* CLI-style progress bar */}
      <div className="relative">
        <div className="h-3 bg-[#21262d] rounded-sm overflow-hidden border border-[#21262d]">
          <motion.div
            className={`h-full ${colors.bar} ${colors.glow}`}
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>

        {/* ASCII-style markers */}
        <div className="flex justify-between text-[8px] text-[#3b3b3b] mt-0.5 font-mono">
          <span>0</span>
          <span>|</span>
          <span>|</span>
          <span>|</span>
          <span>{maxValue}</span>
        </div>
      </div>

      {/* Large value display */}
      {showValue && (
        <div className={`text-2xl font-bold ${colors.text} text-center`}>
          {value.toFixed(1)}
        </div>
      )}
    </div>
  );
}
