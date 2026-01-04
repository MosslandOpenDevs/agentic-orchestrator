'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { SystemStatus } from '@/components/SystemStatus';
import { StatsGrid } from '@/components/Stats';
import { Pipeline } from '@/components/Pipeline';
import { ActivityFeed } from '@/components/ActivityFeed';
import { mockStats, mockActivity, mockPipeline, rssCategories, aiProviders } from '@/data/mock';

export default function Dashboard() {
  const { t } = useI18n();

  return (
    <div className="min-h-screen bg-zinc-950 pt-14">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-mono text-3xl font-bold text-white">
            {t('dashboard.title')}
          </h1>
          <p className="mt-2 text-zinc-400">
            {t('dashboard.subtitle')}
          </p>
          <div className="mt-4">
            <SystemStatus lastRun={mockStats.lastRun} nextRun={mockStats.nextRun} />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <StatsGrid stats={mockStats} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <Pipeline stages={mockPipeline} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          <ActivityFeed activities={mockActivity} />
        </motion.div>

        <div className="grid gap-4 md:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6"
          >
            <h3 className="mb-4 font-mono text-sm text-zinc-500">{t('feeds.title')}</h3>
            <div className="space-y-3">
              {rssCategories.map((cat) => (
                <div key={cat.name} className="flex items-center justify-between">
                  <span className="text-white">{cat.name}</span>
                  <span className="font-mono text-zinc-500">{cat.count} feeds</span>
                </div>
              ))}
            </div>
            <div className="mt-4 border-t border-zinc-800 pt-4 text-center">
              <span className="font-mono text-2xl font-bold text-white">17</span>
              <span className="ml-2 text-zinc-500">{t('feeds.total')}</span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6"
          >
            <h3 className="mb-4 font-mono text-sm text-zinc-500">{t('providers.title')}</h3>
            <div className="space-y-3">
              {aiProviders.map((provider, index) => (
                <motion.div
                  key={provider}
                  className="flex items-center justify-between rounded-lg border border-zinc-700 bg-zinc-800/50 p-3"
                  animate={{
                    borderColor: index === 0 ? ['#3f3f46', '#22c55e', '#3f3f46'] : '#3f3f46',
                  }}
                  transition={{ duration: 3, repeat: Infinity, delay: index }}
                >
                  <span className="text-white">{provider}</span>
                  <motion.div
                    className="h-2 w-2 rounded-full bg-green-500"
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ duration: 2, repeat: Infinity, delay: index * 0.3 }}
                  />
                </motion.div>
              ))}
            </div>
            <div className="mt-4 border-t border-zinc-800 pt-4 text-center text-sm text-zinc-500">
              {t('providers.rotation')}
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 text-center"
        >
          <a
            href="https://github.com/mossland/agentic-orchestrator"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            mossland/agentic-orchestrator
          </a>
        </motion.div>
      </div>
    </div>
  );
}
