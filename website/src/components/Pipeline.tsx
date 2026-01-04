'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { PipelineStage } from '@/lib/types';

interface PipelineProps {
  stages: PipelineStage[];
}

export function Pipeline({ stages }: PipelineProps) {
  const { t } = useI18n();

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <h3 className="mb-6 font-mono text-sm text-zinc-500">{t('pipeline.title')}</h3>
      
      <div className="flex items-center justify-center gap-4">
        {stages.map((stage, index) => (
          <div key={stage.id} className="flex items-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className={`relative flex h-24 w-24 flex-col items-center justify-center rounded-lg border ${
                stage.status === 'active'
                  ? 'border-green-500/50 bg-green-500/10'
                  : stage.status === 'completed'
                  ? 'border-zinc-700 bg-zinc-800/50'
                  : 'border-zinc-800 bg-zinc-900'
              }`}
            >
              {stage.status === 'active' && (
                <motion.div
                  className="absolute inset-0 rounded-lg border border-green-500"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
              <span className="font-mono text-2xl font-bold text-white">{stage.count}</span>
              <span className="mt-1 text-xs text-zinc-500">{stage.name}</span>
            </motion.div>

            {index < stages.length - 1 && (
              <div className="relative mx-2 h-0.5 w-12 bg-zinc-800">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-green-500"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                />
                <motion.div
                  className="absolute top-1/2 h-2 w-2 -translate-y-1/2 rounded-full bg-green-500"
                  animate={{ x: [0, 48, 0] }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-6 flex justify-center gap-6 text-xs text-zinc-600">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span>{t('pipeline.active')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-zinc-700" />
          <span>{t('pipeline.completed')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-zinc-900 ring-1 ring-zinc-800" />
          <span>{t('pipeline.idle')}</span>
        </div>
      </div>
    </div>
  );
}
