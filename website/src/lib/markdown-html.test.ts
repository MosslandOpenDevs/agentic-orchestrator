import assert from 'node:assert/strict';
import { test } from 'node:test';

import { renderMarkdown, safeUrl } from './markdown-html.ts';

// Debate messages are LLM output built from public feeds and are rendered with
// dangerouslySetInnerHTML, so anything that survives this function runs on
// ao.moss.land with the viewer's session.

test('raw HTML is shown as text, not injected as markup', () => {
  const html = renderMarkdown('hello <img src=x onerror=alert(1)> world');

  assert.ok(!html.includes('<img'), html);
  assert.ok(html.includes('&lt;img'), html);
  assert.ok(!html.includes('onerror=alert(1)>'), html);
});

test('script tags do not survive', () => {
  const html = renderMarkdown('# Title\n\n<script>fetch("/steal")</script>');

  assert.ok(!html.includes('<script'), html);
  assert.ok(html.includes('&lt;script'), html);
});

test('event handlers on block-level HTML do not survive', () => {
  const html = renderMarkdown('<div onmouseover="alert(1)">hover</div>');

  assert.ok(!html.includes('<div onmouseover'), html);
  assert.ok(html.includes('&lt;div'), html);
});

test('javascript: links are stripped', () => {
  const html = renderMarkdown('[click me](javascript:alert(1))');

  assert.ok(!html.includes('javascript:'), html);
  assert.ok(html.includes('click me'), html);
});

test('javascript: image sources are stripped', () => {
  const html = renderMarkdown('![alt](javascript:alert(1))');

  assert.ok(!html.includes('javascript:'), html);
});

test('data: URLs are stripped', () => {
  const html = renderMarkdown('[x](data:text/html;base64,PHNjcmlwdD4=)');

  assert.ok(!html.includes('data:text/html'), html);
});

test('scheme obfuscated with control characters is still rejected', () => {
  // Browsers ignore these characters, so the URL parser sees "javascript:".
  assert.equal(safeUrl('java\tscript:alert(1)'), null);
  assert.equal(safeUrl('  javascript:alert(1)'), null);
  assert.equal(safeUrl('java\nscript:alert(1)'), null);
});

test('ordinary links and relative URLs still work', () => {
  const html = renderMarkdown('[docs](https://ao.moss.land/docs) and [rel](/ideas)');

  assert.ok(html.includes('href="https://ao.moss.land/docs"'), html);
  assert.ok(html.includes('href="/ideas"'), html);
});

test('markdown formatting is preserved', () => {
  const html = renderMarkdown('## Heading\n\n- **bold**\n- `code`\n\n> quote');

  assert.ok(html.includes('<h2'), html);
  assert.ok(html.includes('<strong>bold</strong>'), html);
  assert.ok(html.includes('<code>code</code>'), html);
  assert.ok(html.includes('<blockquote>'), html);
});

test('fenced code blocks stay escaped', () => {
  const html = renderMarkdown('```\n<script>alert(1)</script>\n```');

  assert.ok(!html.includes('<script>alert(1)</script>'), html);
  assert.ok(html.includes('&lt;script&gt;'), html);
});

test('empty content renders nothing', () => {
  assert.equal(renderMarkdown(''), '');
});

test('safeUrl keeps the schemes we allow', () => {
  assert.equal(safeUrl('https://example.com'), 'https://example.com');
  assert.equal(safeUrl('mailto:a@b.c'), 'mailto:a@b.c');
  assert.equal(safeUrl('#anchor'), '#anchor');
  assert.equal(safeUrl('../up'), '../up');
  assert.equal(safeUrl(null), null);
});
