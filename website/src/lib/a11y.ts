import type { KeyboardEvent } from 'react';

/**
 * Spreadable props that make a non-button element (e.g. a clickable <div> or
 * framer-motion <motion.div>) behave like a button for keyboard and screen
 * reader users: it becomes focusable, is announced as a button, and activates
 * on Enter/Space in addition to click.
 *
 * Usage: <motion.div {...clickableProps(() => openModal(...))} ... />
 */
export function clickableProps(onActivate: () => void, label?: string | null) {
  return {
    role: 'button' as const,
    tabIndex: 0,
    'aria-label': label ?? undefined,
    onClick: onActivate,
    onKeyDown: (event: KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onActivate();
      }
    },
  };
}
