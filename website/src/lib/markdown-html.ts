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

  // The value goes into an HTML attribute, where the parser decodes character
  // references *before* the URL is parsed. Checking the raw string is not
  // enough on its own: `javascript&#58;alert(1)` has no literal colon, so it
  // reads as scheme-less here and becomes `javascript:alert(1)` in the
  // browser. Escaping the ampersand makes the attribute decode back to
  // exactly the string that was validated -- and closes the whole class,
  // rather than one spelling of it. A real query string survives:
  // `?a=1&b=2` becomes `?a=1&amp;b=2`, which decodes to `?a=1&b=2`.
  return href.trim().replace(/&/g, '&amp;');
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
    // marked's default image renderer interpolates the alt text into
    // `alt="${text}"` without escaping it -- it escapes `title` but not `alt`.
    // A double quote in the alt therefore closes the attribute and everything
    // after it is parsed as further attributes on the <img>, which is a
    // zero-click XSS: the attacker also controls src, so it always fails to
    // load and any injected onerror fires immediately. There is no CSP to
    // fall back on.
    image(token: Tokens.Image) {
      const href = safeUrl(token.href);
      const alt = escapeHtml(token.text ?? '');
      if (!href) return alt;
      const title = token.title ? ` title="${escapeHtml(token.title)}"` : '';
      return `<img src="${escapeHtml(href)}" alt="${alt}"${title}>`;
    },
  },
});

/**
 * Flatten markdown to plain text, for places that render a string as-is.
 *
 * Titles come out of the pipeline as prose, but the translator occasionally
 * keeps the surrounding markdown -- `plan.title_ko` has arrived as
 * `## 계획: ...` -- and a heading rendered into an `<h3>` shows its own `##`.
 * Headings, bullets, emphasis and links are decoration in that position, so
 * strip them rather than teaching every title site to parse markdown.
 *
 * This is not a substitute for `renderMarkdown`: the result is plain text for
 * a JSX text node, never for `dangerouslySetInnerHTML`.
 */
export function stripMarkdown(value: string | null | undefined): string {
  if (!value) return '';

  return (
    value
      // Leading block markers, in the order they can stack: `> ## - text`.
      // A `Plan: ` / `계획: ` prefix may sit in front of them, because backlog
      // triage builds its plan titles as `f"Plan: {idea.title}"` -- when the
      // idea title itself carried a heading the result was `Plan: ## Mossland
      // ...`, which an anchored strip could not match, so the hashes reached
      // the page. That prefix is kept: it is what distinguishes a plan from
      // the idea it came from.
      .replace(/^(\s*(?:Plan|계획)\s*:\s*)?\s*(?:>\s*)*(?:#{1,6}\s+)?(?:[-*+]\s+)?/, '$1')
      // `Idea:` / `아이디어:` carries no information in a position that already
      // says it is showing an idea, and it is what made 431 public issues read
      // `[Idea] Idea: ...`.
      .replace(/^\s*(?:Idea|아이디어)\s*[:：]\s*/i, '')
      .replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1') // links / images -> label
      .replace(/\*\*([^*]+)\*\*/g, '$1') // bold before italic, or the
      .replace(/\*([^*]+)\*/g, '$1') //     inner pair eats the markers
      .replace(/`([^`]+)`/g, '$1')
      // `__bold__` only when it wraps the whole run; a bare `_` is left alone
      // because identifiers (`title_ko`, `idea_id`) legitimately contain it.
      .replace(/__([^_]+)__/g, '$1')
      .replace(/\s+/g, ' ')
      .trim()
  );
}

/**
 * Pick the reader's language for a title, and hand back plain text.
 *
 * Titles are localized and stripped at the same 17 places, and the two steps
 * were separate: `plan.title` was wrapped in `stripMarkdown` while `idea.title`
 * 54 lines above it was not, so ideas rendered their `## Idea:` prefix for
 * months after the identical bug was fixed for plans. One call does both, so
 * there is no second step to forget.
 *
 * Body text keeps using the local `getLocalizedText` -- summaries and
 * descriptions go through `MarkdownContent`, which needs the markup intact.
 */
export function localizedTitle(
  en: string | null | undefined,
  ko: string | null | undefined,
  locale: string,
): string {
  return stripMarkdown(locale === 'ko' && ko ? ko : en);
}

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
