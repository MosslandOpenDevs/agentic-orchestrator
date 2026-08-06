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

// The first version of this sanitizer closed raw HTML and literal
// `javascript:` and stopped there. These are the two holes an adversarial
// review found afterwards; both were live against the deployed renderer.

test('quotes in image alt text cannot break out of the attribute', () => {
  // marked escapes an image's title but not its alt, so a double quote used to
  // close alt="" and everything after it became new attributes on the <img>.
  // Zero-click: the attacker controls src, so it always fails and onerror runs.
  const html = renderMarkdown('![" onerror="alert(1)](/logo.png)');

  assert.ok(!/onerror=["']/.test(html), html);
  assert.ok(html.includes('alt="&quot;'), html);
});

test('reference-style images cannot break out of alt either', () => {
  const html = renderMarkdown('!["onerror="alert(1)][r]\n\n[r]: /x.png');

  assert.ok(!/onerror=["']/.test(html), html);
});

test('an image nested inside a link cannot break out of alt', () => {
  const html = renderMarkdown('[![" onerror="alert(1)](/x.png)](https://ok.dev)');

  assert.ok(!/onerror=["']/.test(html), html);
});

test('image titles are escaped', () => {
  const html = renderMarkdown('![a](/x.png "t\" onerror=\"alert(1)")');

  assert.ok(!/onerror=["']/.test(html), html);
});

test('entity-encoded schemes do not survive attribute decoding', () => {
  // The href goes into an attribute, where the HTML parser decodes character
  // references before the URL is parsed -- so a scheme with no literal colon
  // passed the raw-string check and came back to life in the browser.
  for (const payload of [
    '[c](javascript&#58;alert(1))',
    '[c](&#106;avascript:alert(1))',
    '[c](&#x6A;avascript:alert(1))',
    '[c](javascript&colon;alert(1))',
    '[c][r]\n\n[r]: javascript&#58;alert(1)',
  ]) {
    const html = renderMarkdown(payload);
    // Any & that reaches the attribute must be escaped, so nothing can decode
    // back into a scheme.
    assert.ok(!/href="[^"]*&(?!amp;)/.test(html), `${payload} -> ${html}`);
  }
});

test('query strings still round-trip through the escaping', () => {
  const html = renderMarkdown('[ok](https://x.dev/?a=1&b=2)');

  // &amp; is what the browser decodes back to a bare &.
  assert.ok(html.includes('href="https://x.dev/?a=1&amp;b=2"'), html);
});

test('legitimate images still render', () => {
  const html = renderMarkdown('![a diagram](/img/flow.png "Flow")');

  assert.ok(html.includes('src="/img/flow.png"'), html);
  assert.ok(html.includes('alt="a diagram"'), html);
  assert.ok(html.includes('title="Flow"'), html);
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
