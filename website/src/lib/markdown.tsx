'use client';

import { useMemo } from 'react';

import { localizedTitle, renderMarkdown, stripMarkdown } from './markdown-html';

export { localizedTitle, renderMarkdown, stripMarkdown };

/**
 * Component to render markdown content.
 *
 * The HTML comes from `renderMarkdown`, which escapes raw HTML and rejects
 * unsafe URL schemes -- do not swap in a bare `marked.parse()` here. The
 * content is LLM output derived from public feeds, so it is untrusted input.
 */
export function MarkdownContent({
  content,
  className = ''
}: {
  content: string;
  className?: string;
}) {
  const html = useMemo(() => renderMarkdown(content), [content]);

  return (
    <div
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
