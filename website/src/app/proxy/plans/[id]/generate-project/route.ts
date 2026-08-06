import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.MOSS_BACKEND_URL || 'http://127.0.0.1:3001';

// This route holds the operator's MOSS_API_KEY and spends it on behalf of
// whoever calls it. ao.moss.land is a public dashboard with no user accounts,
// so "the browser never sees the key" (the v0.6.7 goal) is not by itself
// enough: without the guards below, any anonymous POST here makes the server
// run an LLM project generation — GPU time the debate pipeline needs, plus DB
// and disk writes — as often as the caller likes.
//
// Default-deny. The operator opts in only if anonymous visitors really are
// meant to trigger generation; otherwise they call the backend directly with
// the key.
const GENERATION_ENABLED = process.env.MOSS_ENABLE_BROWSER_PROJECT_GENERATION === '1';

// Generation is `project.auto_generate.max_concurrent: 1` upstream, so one
// accepted request per window is the honest ceiling. A process-global limiter
// (not per-IP) is deliberate: behind Nginx the client IP arrives in a header
// the client can forge, and a global cap matches what the backend can do.
const MIN_INTERVAL_MS = 60_000;
let lastAcceptedAt = 0;

// The origin the dashboard is actually served from. Compared against, rather
// than derived from, the request -- deriving it from the Host header would
// mean validating one attacker-supplied header against another.
const PUBLIC_ORIGIN = process.env.MOSS_PUBLIC_ORIGIN || 'https://ao.moss.land';

/**
 * CSRF protection for browser callers. That is all it is.
 *
 * Both headers it reads are set by the browser and cannot be set by page
 * JavaScript, which is what makes them useful against a cross-site request --
 * but any non-browser client sends whatever it likes, so this stops nobody
 * running curl. An earlier version claimed otherwise and was weaker still: it
 * fell back to comparing Origin against Host when Sec-Fetch-Site was absent,
 * which is exactly the case a non-browser client produces, so a single
 * `-H 'Origin: https://ao.moss.land'` satisfied it.
 *
 * What actually keeps an anonymous caller from spending the operator's key is
 * GENERATION_ENABLED being off by default, plus the rate limit below. If this
 * route is ever enabled and anonymous spend is unacceptable, it needs a real
 * credential; no header check can substitute for one.
 */
function isSameOriginBrowserRequest(request: NextRequest): boolean {
  if (request.headers.get('sec-fetch-site') !== 'same-origin') return false;

  const origin = request.headers.get('origin');
  // Same-origin fetches may omit Origin; when present it must be ours.
  return !origin || origin === PUBLIC_ORIGIN;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  if (!GENERATION_ENABLED) {
    return NextResponse.json(
      {
        detail:
          'Project generation is not available from the browser. ' +
          'Set MOSS_ENABLE_BROWSER_PROJECT_GENERATION=1 to enable it.',
      },
      { status: 403 }
    );
  }

  if (!isSameOriginBrowserRequest(request)) {
    return NextResponse.json({ detail: 'Cross-origin request rejected.' }, { status: 403 });
  }

  if (!/^[A-Za-z0-9_-]{1,64}$/.test(id)) {
    return NextResponse.json({ detail: 'Invalid plan id' }, { status: 400 });
  }

  const apiKey = process.env.MOSS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { detail: 'Server is missing MOSS_API_KEY configuration.' },
      { status: 503 }
    );
  }

  const now = Date.now();
  if (now - lastAcceptedAt < MIN_INTERVAL_MS) {
    const retryAfter = Math.ceil((MIN_INTERVAL_MS - (now - lastAcceptedAt)) / 1000);
    return NextResponse.json(
      { detail: 'Project generation was requested too recently.' },
      { status: 429, headers: { 'Retry-After': String(retryAfter) } }
    );
  }
  lastAcceptedAt = now;

  let body: unknown = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const upstream = await fetch(
    `${BACKEND_URL}/plans/${encodeURIComponent(id)}/generate-project`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify(body ?? {}),
    }
  );

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      'Content-Type': upstream.headers.get('Content-Type') ?? 'application/json',
    },
  });
}
