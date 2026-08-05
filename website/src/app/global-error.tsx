'use client';

/**
 * Last-resort boundary for errors thrown in the root layout itself.
 *
 * A route-level error.tsx cannot catch those -- the layout is what renders the
 * boundary -- so without this file a single throw in a layout-level component
 * (for instance while reading a sister service's response) serves a blank
 * page for every route. This keeps the site answering with something readable.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          background: '#0a0a0a',
          color: '#e5e5e5',
          fontFamily:
            'JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace',
          display: 'flex',
          minHeight: '100vh',
          alignItems: 'center',
          justifyContent: 'center',
          margin: 0,
          padding: '2rem',
        }}
      >
        <main style={{ maxWidth: '40rem' }}>
          <p style={{ color: '#ff6b35', fontSize: '0.75rem', letterSpacing: '0.2em' }}>
            MOSS.AO
          </p>
          <h1 style={{ fontSize: '1.25rem', margin: '0.5rem 0 1rem' }}>
            Something went wrong rendering this page.
          </h1>
          <p style={{ color: '#a3a3a3', fontSize: '0.875rem', lineHeight: 1.6 }}>
            The dashboard hit an unexpected error. The orchestrator itself keeps
            running; this is a rendering failure only.
          </p>
          {error.digest ? (
            <p style={{ color: '#737373', fontSize: '0.75rem', marginTop: '1rem' }}>
              digest: {error.digest}
            </p>
          ) : null}
          <button
            onClick={reset}
            style={{
              marginTop: '1.5rem',
              background: 'transparent',
              border: '1px solid #39ff14',
              color: '#39ff14',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              font: 'inherit',
            }}
          >
            $ retry
          </button>
        </main>
      </body>
    </html>
  );
}
