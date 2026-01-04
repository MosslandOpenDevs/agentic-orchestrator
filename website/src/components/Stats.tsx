'use client';

import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect } from 'react';
import { useI18n } from '@/lib/i18n';

interface StatCardProps {
  label: string;
  value: number;
  subValue?: { label: string; value: number };
  icon?: string;
  delay?: number;
}

function AnimatedNumber({ value, delay = 0 }: { value: number; delay?: number }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => Math.round(latest));

  useEffect(() => {
    const timeout = setTimeout(() => {
      const controls = animate(count, value, {
        duration: 1.5,
        ease: 'easeOut',
      });
      return controls.stop;
    }, delay * 1000);

    return () => clearTimeout(timeout);
  }, [count, value, delay]);

  return <motion.span>{rounded}</motion.span>;
}

function StatCard({ label, value, subValue, icon, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1 }}
      whileHover={{ y: -2 }}
      className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500">{label}</span>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="font-mono text-3xl font-bold text-white">
          <AnimatedNumber value={value} delay={delay * 0.1} />
        </span>
        {subValue && (
          <span className="text-sm text-zinc-500">
            (<span className="text-red-400">{subValue.value}</span> {subValue.label})
          </span>
        )}
      </div>
    </motion.div>
  );
}

interface StatsGridProps {
  stats: {
    totalIdeas: number;
    totalPlans: number;
    plansRejected?: number;
    inDevelopment: number;
    trendsAnalyzed: number;
  };
}

export function StatsGrid({ stats }: StatsGridProps) {
  const { t } = useI18n();

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <StatCard label={t('stats.totalIdeas')} value={stats.totalIdeas} icon="💡" delay={0} />
      <StatCard 
        label={t('stats.plansGenerated')} 
        value={stats.totalPlans} 
        subValue={stats.plansRejected ? { label: t('stats.plansRejected'), value: stats.plansRejected } : undefined}
        icon="📋" 
        delay={1} 
      />
      <StatCard label={t('stats.inDevelopment')} value={stats.inDevelopment} icon="⚙️" delay={2} />
      <StatCard label={t('stats.trendsAnalyzed')} value={stats.trendsAnalyzed} icon="📈" delay={3} />
    </div>
  );
}
