import type { Metadata } from 'next';

// Single source of truth for the unified cross-site title/share convention
// (BRIDGE / Algora / MOSS.AO). Every route that declares its own metadata
// must build it from these values — Next.js merges metadata shallowly, so a
// route that restates `openGraph` inline replaces the root object wholesale
// and silently drops shared fields like `siteName` and `images`.
export const SITE_URL = 'https://ao.moss.land';
export const SITE_NAME = 'Mossland';
export const SITE_TITLE = 'MOSS.AO — Agentic Orchestrator · Mossland';
export const TITLE_TEMPLATE = '%s — MOSS.AO · Mossland';
export const SITE_DESCRIPTION =
  'Multi-agent AI orchestration system for Mossland ecosystem';

export const OG_IMAGE = {
  url: '/og-image.png',
  width: 1200,
  height: 630,
  alt: 'Mossland Agentic Orchestrator',
};

type DetailKind = 'Idea' | 'Plan' | 'Project' | 'Signal';

// Share metadata for the /{ideas,plans,projects,signals}/[id] detail routes.
// `title` stays unbranded — the root layout's title.template appends the
// family suffix — while og/twitter titles carry the full string themselves,
// because title.template does not apply to them.
export function detailMetadata(kind: DetailKind, path: string): Metadata {
  const fullTitle = TITLE_TEMPLATE.replace('%s', kind);
  const description = `View ${kind.toLowerCase()} details on MOSS.AO`;

  return {
    title: kind,
    description,
    openGraph: {
      title: fullTitle,
      description,
      url: `${SITE_URL}${path}`,
      siteName: SITE_NAME,
      type: 'website',
      images: [OG_IMAGE],
    },
    twitter: {
      card: 'summary_large_image',
      title: fullTitle,
      description,
    },
  };
}
