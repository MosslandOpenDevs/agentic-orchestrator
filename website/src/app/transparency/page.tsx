'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useI18n } from '@/lib/i18n';
import { ApiClient, type StatusResponse } from '@/lib/api';
import { TerminalWindow } from '@/components/TerminalWindow';

interface TransparencyStats {
  signalsToday: number;
  debatesToday: number;
  ideasGenerated: number;
  plansCreated: number;
  agentsActive: number;
}

export default function TransparencyPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<TransparencyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      const response = await ApiClient.getStatus();
      if (response.data) {
        setStats({
          signalsToday: response.data.stats.signals_today,
          debatesToday: response.data.stats.debates_today,
          ideasGenerated: response.data.stats.ideas_generated,
          plansCreated: response.data.stats.plans_created,
          agentsActive: response.data.stats.agents_active,
        });
      }
      setLoading(false);
    }

    fetchStats();
  }, []);

  const sections = [
    {
      id: 'signals',
      title: t('transparency.signals'),
      description: t('transparency.signalsDesc'),
      icon: '📡',
      color: 'cyan',
      href: '/transparency/signals',
      stat: stats?.signalsToday || 0,
      statLabel: t('transparency.today'),
    },
    {
      id: 'trends',
      title: t('transparency.trends'),
      description: t('transparency.trendsDesc'),
      icon: '📈',
      color: 'purple',
      href: '/trends',
      stat: null,
      statLabel: null,
    },
    {
      id: 'ideas',
      title: t('transparency.ideas'),
      description: t('transparency.ideasDesc'),
      icon: '💡',
      color: 'green',
      href: '/backlog',
      stat: stats?.ideasGenerated || 0,
      statLabel: t('transparency.total'),
    },
    {
      id: 'debates',
      title: t('transparency.debates'),
      description: t('transparency.debatesDesc'),
      icon: '💬',
      color: 'orange',
      href: '/transparency/debates',
      stat: stats?.debatesToday || 0,
      statLabel: t('transparency.today'),
    },
    {
      id: 'plans',
      title: t('transparency.plans'),
      description: t('transparency.plansDesc'),
      icon: '📋',
      color: 'cyan',
      href: '/backlog',
      stat: stats?.plansCreated || 0,
      statLabel: t('transparency.total'),
    },
    {
      id: 'agents',
      title: t('transparency.agents'),
      description: t('transparency.agentsDesc'),
      icon: '🤖',
      color: 'green',
      href: '/agents',
      stat: stats?.agentsActive || 0,
      statLabel: t('transparency.active'),
    },
  ];

  const colorClasses: Record<string, { border: string; text: string; bg: string }> = {
    cyan: {
      border: 'border-[#00ffff]/30 hover:border-[#00ffff]',
      text: 'text-[#00ffff]',
      bg: 'bg-[#00ffff]/5',
    },
    purple: {
      border: 'border-[#bd93f9]/30 hover:border-[#bd93f9]',
      text: 'text-[#bd93f9]',
      bg: 'bg-[#bd93f9]/5',
    },
    green: {
      border: 'border-[#39ff14]/30 hover:border-[#39ff14]',
      text: 'text-[#39ff14]',
      bg: 'bg-[#39ff14]/5',
    },
    orange: {
      border: 'border-[#ff6b35]/30 hover:border-[#ff6b35]',
      text: 'text-[#ff6b35]',
      bg: 'bg-[#ff6b35]/5',
    },
  };

  return (
    <div className="min-h-screen pt-14 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-[#39ff14] mb-2">
            {t('transparency.title')}
          </h1>
          <p className="text-sm text-[#6b7280]">
            {t('transparency.subtitle')}
          </p>
        </motion.div>

        {/* Pipeline Flow Visualization */}
        <TerminalWindow title="ORCHESTRATION_PIPELINE" className="mb-8">
          <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-4 py-4">
            {['Signals', 'Trends', 'Ideas', 'Debates', 'Plans'].map((stage, idx) => (
              <div key={stage} className="flex items-center">
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.1 }}
                  className="px-4 py-2 rounded border border-[#21262d] bg-[#0d1117]"
                >
                  <span className={`text-sm ${idx === 3 ? 'text-[#ff6b35]' : 'text-[#c0c0c0]'}`}>
                    {stage}
                  </span>
                </motion.div>
                {idx < 4 && (
                  <span className="text-[#21262d] mx-1 md:mx-2">→</span>
                )}
              </div>
            ))}
          </div>
        </TerminalWindow>

        {/* Section Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sections.map((section, idx) => {
            const colors = colorClasses[section.color];

            return (
              <motion.div
                key={section.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <Link href={section.href}>
                  <div
                    className={`
                      card-cli p-6 h-full cursor-pointer transition-all duration-300
                      ${colors.border} ${colors.bg}
                      hover:shadow-lg hover:scale-[1.02]
                    `}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="text-3xl">{section.icon}</div>
                      {section.stat !== null && (
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${colors.text}`}>
                            {loading ? '...' : section.stat}
                          </div>
                          <div className="text-[10px] text-[#6b7280]">
                            {section.statLabel}
                          </div>
                        </div>
                      )}
                    </div>

                    <h3 className={`text-lg font-bold mb-2 ${colors.text}`}>
                      {section.title}
                    </h3>
                    <p className="text-sm text-[#6b7280] leading-relaxed">
                      {section.description}
                    </p>

                    <div className="mt-4 flex items-center text-xs text-[#6b7280]">
                      <span>{t('transparency.viewDetails')}</span>
                      <span className="ml-2">→</span>
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>

        {/* Info Box */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8"
        >
          <TerminalWindow title="INFO">
            <div className="text-xs text-[#6b7280] space-y-2">
              <p>
                <span className="text-[#00ffff]">$</span> {t('transparency.info1')}
              </p>
              <p>
                <span className="text-[#00ffff]">$</span> {t('transparency.info2')}
              </p>
            </div>
          </TerminalWindow>
        </motion.div>
      </div>
    </div>
  );
}
