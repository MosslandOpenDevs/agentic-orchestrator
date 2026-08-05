import { marked, type Token, type Tokens } from 'marked';

/**
 * Markdown -> HTML for content this site does not control.
 *
 * Debate messages, ideas and plans are written by an LLM whose prompt is built
 * from RSS items, GitHub issues and other public feeds, and the result is
 * injected with `dangerouslySetInnerHTML`. `marked` does not sanitize -- its
 * `sanitize` option was removed in v5 -- so raw HTML in a model response used
 * to execute on ao.moss.land.
 *
 * Two holes are closed here, both at the token level so every renderer path
 * inherits them:
 *
 * 1. Raw HTML (`<img onerror=...>`) is emitted as visible text, not markup.
 * 2. Link and image URLs are restricted to safe schemes, because marked's
 *    `cleanUrl` only runs the href through `encodeURI` -- which leaves
 *    `javascript:` intact.
 */

const HTML_ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => HTML_ESCAPES[char]);
}

// Anything that is not a scheme (relative, absolute-path, fragment) is fine;
// of the schemes, only these cannot run code in the page.
const SAFE_SCHEME = /^(?:https?|mailto|tel|ftp):/i;
const HAS_SCHEME = /^[a-z][a-z0-9+.-]*:/i;
// Browsers ignore control characters and spaces inside a URL, so
// "java\tscript:..." reaches the URL parser as "javascript:".
const CONTROL_OR_SPACE = /[\x00-\x20]/g;

export function safeUrl(href: string | null | undefined): string | null {
  if (!href) return null;

  const probe = href.replace(CONTROL_OR_SPACE, '');
  if (!probe) return null;
  if (HAS_SCHEME.test(probe) && !SAFE_SCHEME.test(probe)) return null;
  return href.trim();
}

marked.use({
  breaks: true, // Convert \n to <br>
  gfm: true, // GitHub Flavored Markdown
  walkTokens(token: Token) {
    if (token.type === 'link' || token.type === 'image') {
      const linkish = token as Tokens.Link | Tokens.Image;
      linkish.href = safeUrl(linkish.href) ?? '';
    }
  },
  renderer: {
    // Block-level and inline raw HTML both arrive here.
    html(token: Tokens.HTML | Tokens.Tag) {
      return escapeHtml(token.raw);
    },
  },
});

/**
 * Render markdown content to a sanitized HTML string.
 */
export function renderMarkdown(content: string): string {
  if (!content) return '';

  try {
    return marked.parse(content, { async: false }) as string;
  } catch {
    // Never fall back to the raw string: the caller inserts the result
    // unescaped, which is the very thing this module exists to prevent.
    return escapeHtml(content);
  }
}
