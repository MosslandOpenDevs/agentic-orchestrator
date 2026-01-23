'use client';

import { motion } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import { DebateVisualization } from '@/components/DebateVisualization';

export default function SystemPage() {
  const { t } = useI18n();

  const pipelineStages = [
    { id: 'ideation', name: 'IDEATION', desc: t('system.stage.ideation'), color: 'bg-yellow-500' },
    { id: 'planning-draft', name: 'PLANNING_DRAFT', desc: t('system.stage.planningDraft'), color: 'bg-orange-500' },
    { id: 'planning-review', name: 'PLANNING_REVIEW', desc: t('system.stage.planningReview'), color: 'bg-purple-500' },
    { id: 'dev', name: 'DEV', desc: t('system.stage.dev'), color: 'bg-blue-500' },
    { id: 'qa', name: 'QA', desc: t('system.stage.qa'), color: 'bg-cyan-500' },
    { id: 'done', name: 'DONE', desc: t('system.stage.done'), color: 'bg-green-500' },
  ];

  const techStack = [
    { category: 'LLM Providers', items: ['Claude (Anthropic)', 'GPT-5.2 (OpenAI)', 'Gemini (Google)'] },
    { category: 'Data Sources', items: ['17 RSS Feeds', 'GitHub Issues API', 'GitHub Actions'] },
    { category: 'Storage', items: ['GitHub Issues (Backlog)', 'Markdown + YAML (Trends)', 'YAML (State)'] },
    { category: 'Automation', items: ['GitHub Actions (Daily 08:00 KST)', 'Label-based Promotion', 'File Lock'] },
  ];

  const workflowSteps = [
    { num: '1', title: t('system.workflow.1'), desc: t('system.workflow.1.desc') },
    { num: '2', title: t('system.workflow.2'), desc: t('system.workflow.2.desc') },
    { num: '3', title: t('system.workflow.3'), desc: t('system.workflow.3.desc') },
    { num: '4', title: t('system.workflow.4'), desc: t('system.workflow.4.desc') },
    { num: '5', title: t('system.workflow.5'), desc: t('system.workflow.5.desc') },
    { num: '6', title: t('system.workflow.6'), desc: t('system.workflow.6.desc') },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 pt-14">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-mono text-3xl font-bold text-white">{t('system.title')}</h1>
          <p className="mt-2 text-zinc-400">{t('system.subtitle')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="mb-4 font-mono text-sm text-zinc-500">{t('system.pipelineStages')}</h2>
          <div className="flex flex-wrap gap-2">
            {pipelineStages.map((stage, index) => (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center gap-3"
              >
                <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-3">
                  <div className="flex items-center gap-2">
                    <div className={`h-2 w-2 rounded-full ${stage.color}`} />
                    <span className="font-mono text-xs text-white">{stage.name}</span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-500">{stage.desc}</div>
                </div>
                {index < pipelineStages.length - 1 && (
                  <span className="text-zinc-600">→</span>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <DebateVisualization />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          <h2 className="mb-4 font-mono text-sm text-zinc-500">{t('system.techStack')}</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {techStack.map((stack, index) => (
              <motion.div
                key={stack.category}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.05 }}
                className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
              >
                <h3 className="mb-3 font-mono text-xs text-zinc-500">{stack.category}</h3>
                <div className="space-y-2">
                  {stack.items.map((item) => (
                    <div
                      key={item}
                      className="flex items-center gap-2 text-sm text-zinc-300"
                    >
                      <span className="text-green-500">•</span>
                      {item}
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6"
        >
          <h2 className="mb-4 font-mono text-sm text-zinc-500">{t('system.workflow')}</h2>
          <div className="space-y-4 font-mono text-sm">
            {workflowSteps.map((step) => (
              <div key={step.num} className="flex items-start gap-4">
                <span className="text-green-500">{step.num}.</span>
                <div>
                  <span className="text-white">{step.title}</span>
                  <span className="ml-2 text-zinc-500">→ {step.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <a
            href="https://github.com/MosslandOpenDevs/agentic-orchestrator"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-300"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            {t('common.viewSource')}
          </a>
        </motion.div>
      </div>
    </div>
  );
}
