'use client';

import { useEffect, useCallback, useRef, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n';
import type { ModalType, ModalData } from './ModalProvider';

// Import detail components (to be created)
import { SignalDetail } from '../details/SignalDetail';
import { TrendDetail } from '../details/TrendDetail';
import { IdeaDetail } from '../details/IdeaDetail';
import { DebateDetail } from '../details/DebateDetail';
import { PlanDetail } from '../details/PlanDetail';
import { ProjectDetail } from '../details/ProjectDetail';
import { AgentDetail } from '../details/AgentDetail';
import { StatsDetail } from '../details/StatsDetail';
import { PipelineDetail } from '../details/PipelineDetail';

interface TerminalModalProps {
  type: ModalType;
  data: ModalData;
  onClose: () => void;
}

// Map modal types to their detail components
function getDetailComponent(type: ModalType, data: ModalData): ReactNode {
  switch (type) {
    case 'signal':
      return <SignalDetail data={data} />;
    case 'trend':
      return <TrendDetail data={data} />;
    case 'idea':
      return <IdeaDetail data={data} />;
    case 'debate':
      return <DebateDetail data={data} />;
    case 'plan':
      return <PlanDetail data={data} />;
    case 'project':
      return <ProjectDetail data={data} />;
    case 'agent':
      return <AgentDetail data={data} />;
    case 'stats':
      return <StatsDetail data={data} />;
    case 'pipeline':
      return <PipelineDetail data={data} />;
    default:
      return null;
  }
}

// Modal type titles
function getModalTitle(type: ModalType, t: (key: string) => string): string {
  const titles: Record<ModalType, string> = {
    signal: t('modal.signal.title'),
    trend: t('modal.trend.title'),
    idea: t('modal.idea.title'),
    debate: t('modal.debate.title'),
    plan: t('modal.plan.title'),
    project: t('modal.project.title'),
    agent: t('modal.agent.title'),
    stats: t('modal.stats.title'),
    pipeline: t('modal.pipeline.title'),
  };
  return titles[type];
}

// Modal type colors
function getModalColor(type: ModalType): string {
  const colors: Record<ModalType, string> = {
    signal: 'cyan',
    trend: 'purple',
    idea: 'green',
    debate: 'orange',
    plan: 'cyan',
    project: 'green',
    agent: 'green',
    stats: 'cyan',
    pipeline: 'green',
  };
  return colors[type];
}

export function TerminalModal({ type, data, onClose }: TerminalModalProps) {
  const { t } = useI18n();
  const dialogRef = useRef<HTMLDivElement>(null);

  // ESC to close + Tab focus trap within the dialog.
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key === 'Tab' && dialogRef.current) {
        const focusable = Array.from(
          dialogRef.current.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
          )
        ).filter((el) => el.offsetParent !== null || el === document.activeElement);
        // No focusable children: keep focus on the dialog itself.
        if (focusable.length === 0) {
          event.preventDefault();
          dialogRef.current.focus();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement;
        const insideDialog = dialogRef.current.contains(active);
        // Wrap at the edges, and pull focus back in if it escaped (or sits on
        // the dialog container, which has tabindex=-1).
        if (event.shiftKey) {
          if (!insideDialog || active === first) {
            event.preventDefault();
            last.focus();
          }
        } else if (!insideDialog || active === last) {
          event.preventDefault();
          first.focus();
        }
      }
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Lock background scroll, move focus into the dialog, and restore focus on close.
  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    document.body.style.overflow = 'hidden';
    dialogRef.current?.focus();
    return () => {
      // Reset to the default (visible) rather than a captured value: the app only
      // ever locks body scroll for modals, so this can't leave it stuck hidden.
      document.body.style.overflow = '';
      previouslyFocused?.focus?.();
    };
  }, []);

  // Handle outside click
  const handleOverlayClick = (event: React.MouseEvent) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const color = getModalColor(type);
  const title = data.title || getModalTitle(type, t);

  return (
    <AnimatePresence>
      <motion.div
        className="modal-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleOverlayClick}
      >
        {/* Scanline overlay effect */}
        <div className="modal-scanline" />

        <motion.div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label={`${type.toUpperCase()}: ${title}`}
          tabIndex={-1}
          className="modal-container"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        >
          {/* Terminal window frame */}
          <div className={`terminal-window modal-window modal-border-${color}`}>
            {/* Header */}
            <div className="terminal-header modal-header">
              <div className="flex gap-1.5">
                <button
                  onClick={onClose}
                  className="terminal-dot red hover:brightness-125 transition-all cursor-pointer"
                  title={t('modal.close')}
                  aria-label={t('modal.close')}
                />
                <div className="terminal-dot yellow" />
                <div className="terminal-dot green" />
              </div>
              <div className="flex-1 text-center">
                <span className={`text-xs tracking-wider uppercase glow-${color}`}>
                  [{type.toUpperCase()}] {title}
                </span>
              </div>
              <div className="w-[52px] flex justify-end">
                <span className="text-[10px] text-[#8b949e]">ESC</span>
              </div>
            </div>

            {/* Body */}
            <div className="terminal-body modal-body">
              {getDetailComponent(type, data)}
            </div>

            {/* Footer */}
            <div className="modal-footer">
              <div className="flex items-center justify-between text-[10px] text-[#8b949e]">
                <span>ID: {data.id}</span>
                <button
                  onClick={onClose}
                  className="btn-cli text-[10px] py-1 px-3"
                >
                  {t('modal.close')}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
