import { ImageResponse } from 'next/og';

/**
 * Social preview card.
 *
 * The metadata used to point at /og-image.png, which does not exist in
 * public/ or as a route -- every share of ao.moss.land requested a 404 and
 * rendered without a preview. Generating it here keeps the asset and the
 * metadata from drifting apart again.
 */

export const alt = 'MOSS.AO — Agentic Orchestrator · Mossland';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          padding: '80px',
          background: '#0d1117',
          color: '#c0c0c0',
          fontFamily: 'monospace',
        }}
      >
        <div style={{ display: 'flex', fontSize: 28, color: '#39ff14', letterSpacing: 8 }}>
          MOSSLAND
        </div>
        <div
          style={{
            display: 'flex',
            fontSize: 96,
            fontWeight: 700,
            color: '#ffffff',
            marginTop: 16,
          }}
        >
          MOSS.AO
        </div>
        <div style={{ display: 'flex', fontSize: 36, color: '#00ffff', marginTop: 8 }}>
          Agentic Orchestrator
        </div>
        <div style={{ display: 'flex', fontSize: 28, color: '#8b949e', marginTop: 32 }}>
          Multi-agent AI orchestration for the Mossland ecosystem
        </div>
        <div style={{ display: 'flex', fontSize: 24, color: '#ff6b35', marginTop: 48 }}>
          ao.moss.land
        </div>
      </div>
    ),
    size
  );
}
