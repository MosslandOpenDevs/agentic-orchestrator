/**
 * Parsing for the npc.moss.land headline feed.
 *
 * The consumer (`NpcCityStrip`) is a server component in the root layout with
 * no error boundary above it, so a throw while reading this payload blanks
 * every page of the site -- for data owned by a different service. The payload
 * used to be cast straight to `Headline[]`, which meant a *successful*
 * response in an unexpected shape (`{"headlines": {}}`, or a record with no
 * `npc`) threw on `.length` / `.slice` / field access, outside the fetch's
 * try/catch. Nothing here throws: unusable records are dropped.
 */

export type Headline = {
  npc: {
    slug: string;
    name: string;
    role: string;
    accent_color?: string | null;
    portrait_url?: string | null;
  };
  text: string;
  date: string;
};

const SAFE_SLUG = /^[A-Za-z0-9_-]{1,64}$/;
const SAFE_COLOR = /^(#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20})$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function str(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

/** A path on the NPC host, never an absolute or traversing URL: the value is
 *  concatenated onto the base, so "https://elsewhere/..." must not pass. */
export function safePath(value: unknown): string | null {
  if (typeof value !== "string") return null;
  if (!value.startsWith("/") || value.startsWith("//") || value.includes("..")) return null;
  return value;
}

/** Accept only records the strip can actually render; otherwise null. */
export function toHeadline(value: unknown): Headline | null {
  if (!isRecord(value) || !isRecord(value.npc)) return null;

  const npc = value.npc;
  const slug = str(npc.slug);
  const name = str(npc.name);
  const text = str(value.text);
  if (!SAFE_SLUG.test(slug) || !name || !text) return null;

  const accent = str(npc.accent_color);
  return {
    npc: {
      slug,
      name,
      role: str(npc.role),
      accent_color: SAFE_COLOR.test(accent) ? accent : null,
      portrait_url: safePath(npc.portrait_url),
    },
    text,
    date: str(value.date),
  };
}

/** Extract the renderable headlines from an arbitrary JSON payload. */
export function parseHeadlines(payload: unknown): Headline[] {
  const raw = isRecord(payload) ? payload.headlines : null;
  if (!Array.isArray(raw)) return [];
  return raw.map(toHeadline).filter((h): h is Headline => h !== null);
}
