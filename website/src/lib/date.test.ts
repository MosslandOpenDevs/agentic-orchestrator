// The timezone is pinned by the test, not by the runner. This regression does
// not reproduce under TZ=UTC -- every wrong answer is also the right answer
// there -- so a CI runner in UTC (ubuntu-latest, which is what .github/
// workflows/ci.yml uses) would run a green suite over a broken dashboard.
// Assigning process.env.TZ before anything reads a clock re-homes Node's clock
// for the whole file; verified to take effect even when the ambient TZ is UTC.
process.env.TZ = 'Asia/Seoul';

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { parseUTCDate } from './date.ts';

// Every timestamp on this site comes from AO's own API, which stores UTC.
// The failure this file exists for is silent: a marker-less string parsed as
// local time stays entirely plausible and is merely nine hours away from what
// it says, so a signal collected 24 minutes ago renders as "about 9 hours ago"
// and the pipeline looks dead. Measured on ao.moss.land, 2026-09-09.

test('a backend timestamp with no marker is an instant, not the viewer wall clock', () => {
  assert.equal(parseUTCDate('2026-09-10T00:55:00')!.toISOString(), '2026-09-10T00:55:00.000Z');
});

test('microseconds do not change that (what SQLite actually stores)', () => {
  assert.equal(
    parseUTCDate('2026-09-09T03:35:06.440822')!.toISOString(),
    '2026-09-09T03:35:06.440Z'
  );
});

test('a marked timestamp is left alone, so the helper is safe to apply twice', () => {
  // The backend marks its instants now. This is what makes adopting the helper
  // at a call site a no-op rather than a double correction.
  assert.equal(parseUTCDate('2026-09-10T00:55:00Z')!.toISOString(), '2026-09-10T00:55:00.000Z');
});

test('an explicit offset is honoured rather than overridden', () => {
  assert.equal(
    parseUTCDate('2026-09-10T00:55:00+09:00')!.toISOString(),
    '2026-09-09T15:55:00.000Z'
  );
  assert.equal(
    parseUTCDate('2026-09-10T00:55:00-05:00')!.toISOString(),
    '2026-09-10T05:55:00.000Z'
  );
});

test('a date-only value survives (the /usage history rows are date-only)', () => {
  assert.equal(parseUTCDate('2026-09-10')!.toISOString(), '2026-09-10T00:00:00.000Z');
});

test('nothing in means nothing out, never the current time', () => {
  for (const empty of [null, undefined, '']) {
    assert.equal(parseUTCDate(empty), null, JSON.stringify(empty));
  }
});
