/**
 * Cross-link strip surfacing live npc.moss.land resident headlines.
 *
 * Mounted on each sister-site layout above the footer to give curious
 * readers a "before you leave" hook into the NPC city. Server-rendered
 * with a 10-min revalidate so it doesn't hammer the npc backend on
 * every pageview, plus a 4 s timeout fallback to nothing — a sister
 * service hiccup never breaks this site's rendering.
 *
 * Stylistically neutral on purpose: subtle translucent surface +
 * inline-styled NPC accent colors. Works on both dark and light
 * parent themes without forcing a dark-mode toggle.
 */
import Link from "next/link";

type Headline = {
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

const NPC_BASE = "https://npc.moss.land";

async function fetchHeadlines(): Promise<Headline[]> {
  try {
    const res = await fetch(`${NPC_BASE}/api/headlines/today`, {
      next: { revalidate: 600 },
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return [];
    const data = (await res.json()) as { headlines?: Headline[] };
    return data.headlines ?? [];
  } catch {
    return [];
  }
}

export async function NpcCityStrip() {
  const headlines = await fetchHeadlines();
  if (headlines.length === 0) return null;
  const picked = headlines.slice(0, 3);

  return (
    <section className="border-t border-zinc-500/15 bg-zinc-500/[0.04]">
      <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-8">
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <p className="text-[10.5px] uppercase tracking-[0.22em] text-zinc-500">
              모스랜드 NPC · 오늘의 도시
            </p>
            <h2 className="mt-1 text-[15px] font-semibold text-zinc-700 dark:text-zinc-200">
              주민들이 오늘 들은 신호로 한 마디씩.
            </h2>
          </div>
          <Link
            href={NPC_BASE}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[12px] text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-100 shrink-0"
          >
            도시 가기 ↗
          </Link>
        </div>
        <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
          {picked.map((h) => {
            const accent = h.npc.accent_color ?? "#f59e0b";
            return (
              <li key={h.npc.slug}>
                <Link
                  href={`${NPC_BASE}/npc/${h.npc.slug}/wall`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex h-full gap-2.5 rounded-xl border border-zinc-500/15 bg-zinc-500/[0.04] p-2.5 transition hover:border-zinc-500/40"
                >
                  {h.npc.portrait_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`${NPC_BASE}${h.npc.portrait_url}`}
                      alt={h.npc.name}
                      className="h-10 w-10 shrink-0 rounded-lg object-cover ring-1"
                      style={{ borderColor: accent }}
                    />
                  ) : (
                    <div
                      className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-sm font-bold text-white"
                      style={{ backgroundColor: accent }}
                    >
                      {h.npc.name.charAt(0)}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-baseline gap-1.5">
                      <span
                        className="text-[10.5px] font-semibold tracking-wide"
                        style={{ color: accent }}
                      >
                        {h.npc.name}
                      </span>
                      <span className="truncate text-[10px] text-zinc-500">
                        {h.npc.role}
                      </span>
                    </div>
                    <p className="mt-0.5 line-clamp-3 text-[12px] leading-snug text-zinc-700 dark:text-zinc-200">
                      {h.text}
                    </p>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
