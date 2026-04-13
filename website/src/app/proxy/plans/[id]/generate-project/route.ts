import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.MOSS_BACKEND_URL || 'http://127.0.0.1:3001';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

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
