'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useI18n, LanguageToggle } from '@/lib/i18n';

export function Navigation() {
  const pathname = usePathname();
  const { t } = useI18n();

  const navItems = [
    { href: '/', label: t('nav.dashboard') },
    { href: '/trends', label: t('nav.trends') },
    { href: '/backlog', label: t('nav.backlog') },
    { href: '/system', label: t('nav.system') },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="font-mono text-lg font-bold text-white">Mossland</span>
          <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-400">
            AO
          </span>
        </Link>

        <div className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="relative px-3 py-2 text-sm transition-colors"
              >
                <span className={isActive ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'}>
                  {item.label}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute inset-x-1 -bottom-px h-0.5 bg-green-500"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-3">
          <LanguageToggle />
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="h-2 w-2 rounded-full bg-green-500"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.6, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
            <span className="font-mono text-xs text-green-500">{t('nav.running')}</span>
          </motion.div>
        </div>
      </div>
    </nav>
  );
}
