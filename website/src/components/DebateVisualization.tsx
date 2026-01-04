'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { aiProviders } from '@/data/mock';

export function DebateVisualization() {
  const { t } = useI18n();

  const debateRoles = [
    { name: t('role.founder'), perspective: t('role.founder.perspective'), icon: '🚀' },
    { name: t('role.vc'), perspective: t('role.vc.perspective'), icon: '💰' },
    { name: t('role.accelerator'), perspective: t('role.accelerator.perspective'), icon: '⚡' },
    { name: t('role.founderFriend'), perspective: t('role.founderFriend.perspective'), icon: '🤝' },
  ];

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <h3 className="mb-6 font-mono text-sm text-zinc-500">{t('system.debate.title')}</h3>

      <div className="flex flex-col items-center gap-4">
        {debateRoles.map((role, index) => (
          <motion.div
            key={role.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="relative w-full max-w-md"
          >
            <div className="flex items-center gap-4 rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-700 text-2xl">
                {role.icon}
              </div>
              <div className="flex-1">
                <div className="font-medium text-white">{role.name}</div>
                <div className="text-sm text-zinc-400">{role.perspective}</div>
              </div>
              <div className="flex gap-1">
                {aiProviders.map((provider, i) => (
                  <motion.div
                    key={provider}
                    className={`rounded px-2 py-1 text-xs ${
                      i === index % 3
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-zinc-700 text-zinc-500'
                    }`}
                    animate={
                      i === index % 3
                        ? { scale: [1, 1.05, 1] }
                        : {}
                    }
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    {provider}
                  </motion.div>
                ))}
              </div>
            </div>

            {index < debateRoles.length - 1 && (
              <div className="flex justify-center py-2">
                <motion.div
                  className="h-6 w-0.5 bg-zinc-700"
                  initial={{ scaleY: 0 }}
                  animate={{ scaleY: 1 }}
                  transition={{ delay: index * 0.1 + 0.3 }}
                />
              </div>
            )}
          </motion.div>
        ))}

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4 rounded-lg border border-green-500/30 bg-green-500/10 px-6 py-3"
        >
          <span className="font-mono text-green-400">→ {t('system.planGenerated')}</span>
        </motion.div>
      </div>

      <div className="mt-6 border-t border-zinc-800 pt-4 text-center text-sm text-zinc-500">
        {t('system.debate.rotation')}
      </div>
    </div>
  );
}
