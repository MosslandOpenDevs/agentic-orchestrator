import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

// A number on this site is a claim about the system. These two patterns are how
// the site has repeatedly ended up making claims nothing measured:
//
//   `Math.random()` inside a chart, which produced a plausible histogram out of
//   nothing and re-rolled it on every render, and
//
//   a dollar figure written as a string literal in JSX -- `$50.00` for a limit
//   configured at $3.00, `$12.45` for a spend measured at $0.65.
//
// Neither fails loudly: an invented chart looks exactly like a measured one,
// which is worse than an empty one. Both checks are deliberately blunt, and
// both are satisfied by *deleting* the claim, not by approximating it better.

const SRC = path.join(import.meta.dirname, '..');

function sourceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return sourceFiles(full);
    if (!/\.tsx?$/.test(entry.name) || entry.name.endsWith('.test.ts')) return [];
    return [full];
  });
}

/** Strip block and line comments, so the notes explaining these rules -- which
 *  necessarily quote the patterns -- do not trip the rules. */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
}

const FILES = sourceFiles(SRC);

test('the source tree is actually being scanned', () => {
  // Guards the whole file: a broken walk would make every assertion below pass.
  assert.ok(FILES.length > 40, `only found ${FILES.length} files under ${SRC}`);
});

test('no chart invents its own data with Math.random()', () => {
  const offenders = FILES.filter((file) =>
    withoutComments(readFileSync(file, 'utf8')).includes('Math.random(')
  ).map((file) => path.relative(SRC, file));

  assert.deepEqual(
    offenders,
    [],
    'a rendered value must come from the API. If there is no data, render the ' +
      'empty state -- an invented chart is indistinguishable from a measured one.'
  );
});

test('no dollar figure is hard-coded into the markup', () => {
  const offenders: string[] = [];
  // .tsx only: this is about what gets rendered, and a regex replacement
  // string in a .ts helper ('$1') is not a price.
  for (const file of FILES.filter((f) => f.endsWith('.tsx'))) {
    const lines = withoutComments(readFileSync(file, 'utf8')).split('\n');
    lines.forEach((line, i) => {
      // `$12.45` written out, as opposed to `${formatCost(x)}` or `$${cost}`.
      // Cents are required: that is the shape a published price takes, and it
      // keeps Tailwind classes and template fragments out of the result.
      if (/\$\d[\d,]*\.\d\d\b/.test(line.replace(/\$\{[^}]*\}/g, ''))) {
        offenders.push(`${path.relative(SRC, file)}:${i + 1}: ${line.trim()}`);
      }
    });
  }

  assert.deepEqual(
    offenders,
    [],
    'spend and budget figures belong to /usage and config.yaml. A literal here ' +
      'drifts from both silently -- the last pair was off by 16x and 19x.'
  );
});
