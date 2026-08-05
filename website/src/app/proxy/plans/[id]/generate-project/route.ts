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

function isSameOrigin(request: NextRequest): boolean {
  // Browsers send Sec-Fetch-Site on every fetch; same-origin is what our own
  // UI produces. Absent that, fall back to comparing Origin with Host, which
  // also rejects a cross-site form post. A client sending neither (curl) is
  // not our UI and has no business using the server's key.
  const fetchSite = request.headers.get('sec-fetch-site');
  if (fetchSite) return fetchSite === 'same-origin';

  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host;
  } catch {
    return false;
  }
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

  if (!isSameOrigin(request)) {
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
