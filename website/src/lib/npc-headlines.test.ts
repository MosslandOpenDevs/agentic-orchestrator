import assert from 'node:assert/strict';
import { test } from 'node:test';

import { parseHeadlines, safePath, toHeadline } from './npc-headlines.ts';

const VALID = {
  npc: {
    slug: 'mossy',
    name: 'Mossy',
    role: 'Archivist',
    accent_color: '#39ff14',
    portrait_url: '/portraits/mossy.png',
  },
  text: 'Signals are loud today.',
  date: '2026-08-06',
};

// npc.moss.land is a different service. Whatever it returns, this site's root
// layout has to keep rendering.

test('a well-formed payload parses', () => {
  const parsed = parseHeadlines({ headlines: [VALID] });

  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].npc.slug, 'mossy');
  assert.equal(parsed[0].npc.portrait_url, '/portraits/mossy.png');
});

test('headlines that are not an array yield nothing instead of throwing', () => {
  for (const payload of [
    { headlines: {} },
    { headlines: null },
    { headlines: 'nope' },
    {},
    null,
    'a string',
    42,
  ]) {
    assert.deepEqual(parseHeadlines(payload), [], JSON.stringify(payload));
  }
});

test('records missing npc or text are dropped, not rendered', () => {
  const parsed = parseHeadlines({
    headlines: [{ text: 'orphan' }, { npc: null }, { npc: {} }, null, 'x', VALID],
  });

  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].npc.name, 'Mossy');
});

test('a slug that could reshape the link is rejected', () => {
  assert.equal(toHeadline({ ...VALID, npc: { ...VALID.npc, slug: '../../evil' } }), null);
  assert.equal(toHeadline({ ...VALID, npc: { ...VALID.npc, slug: 'a/b' } }), null);
  assert.equal(toHeadline({ ...VALID, npc: { ...VALID.npc, slug: '' } }), null);
});

test('portrait_url is restricted to a path on the NPC host', () => {
  // It is concatenated onto the base URL, so an absolute URL must not pass.
  assert.equal(safePath('https://evil.example/x.png'), null);
  assert.equal(safePath('//evil.example/x.png'), null);
  assert.equal(safePath('/../../etc/passwd'), null);
  assert.equal(safePath('relative.png'), null);
  assert.equal(safePath(42), null);
  assert.equal(safePath('/portraits/ok.png'), '/portraits/ok.png');
});

test('a junk accent colour falls back instead of reaching the style attribute', () => {
  const parsed = toHeadline({
    ...VALID,
    npc: { ...VALID.npc, accent_color: 'url(javascript:alert(1))' },
  });

  assert.ok(parsed);
  assert.equal(parsed.npc.accent_color, null);
});

test('missing optional fields become safe defaults', () => {
  const parsed = toHeadline({ npc: { slug: 'a', name: 'A' }, text: 'hi' });

  assert.ok(parsed);
  assert.equal(parsed.npc.role, '');
  assert.equal(parsed.npc.portrait_url, null);
  assert.equal(parsed.npc.accent_color, null);
  assert.equal(parsed.date, '');
});
