# Memo: shared Ollama GPU contention between Algora and MOSS.AO

**To:** Algora team
**From:** MOSS.AO (agentic-orchestrator)
**Date:** 2026-08-06
**Ask:** one env var change on your side — `LOCAL_LLM_NUM_CTX=16384`

---

## Summary

Our two services share the Ollama host at `192.168.1.65:11434`, and we request
the **same model at different context sizes**. In Ollama each distinct
`num_ctx` is a *separate model instance*, so whichever of us is resident wins
and the other blocks on a model load that, under contention, does not complete.

Since roughly 2026-08-05 midday this has cost MOSS.AO its entire local-LLM
pipeline: three debates died after ~90 minutes each, trend analysis saved zero
trends on repeated runs, and idea triage timed out at 1800s per item. We are
not reporting a fault on your side — the configuration is reasonable in
isolation, and ours was equally unilateral. We just cannot both pick a number.

## Measurements

Taken from `atrn-vm-linux` against the shared host on 2026-08-06 04:10 UTC.

**Only the resident context size responds. Every other size hangs.**

| requested `num_ctx` | result |
|---|---|
| 8192 (currently resident) | HTTP 200 in **0.7 s** |
| 4096 | timeout (no response in 40 s) |
| 16384 | timeout (no response in 40 s) |
| omitted (server default 4096) | timeout (no response in 30 s) |

**This is not a capacity problem.** The card is ~8 GB and only 3.03 GB is in
use — about 5 GB free. The block is on loading a second instance, not on
memory.

**The resident instance is continuously refreshed:**

| server time (UTC) | `expires_at` (UTC) | remaining |
|---|---|---|
| 04:10:23 | 04:25:11 | 14 min 48 s |
| 04:11:53 | 04:26:42 | 14 min 49 s |

Expiry advanced 91 s over 90 s of wall clock — so inference calls arrive at
least every ~90 s, each renewing the 15-minute `keep_alive`. In practice the
8192 instance is permanently resident.

## Where the two configurations differ

| | Algora | MOSS.AO |
|---|---|---|
| model | `gemma3:4b` | `gemma3:4b` |
| `num_ctx` | **8192** (`apps/api/src/services/llm.ts`, `LOCAL_LLM_NUM_CTX` default) | **16384** (`config.yaml` `throttling.ollama.num_ctx`) |
| `keep_alive` | `15m` | not set (server default) |

Same host, same model, different context — which is exactly the condition that
forces a reload on every alternation.

## What we are asking for

Set `LOCAL_LLM_NUM_CTX=16384` in Algora's environment.

Your own code comments already anticipate this ("Raise via env if prompts
grow", `llm.ts`), so no code change is needed.

**Why this direction rather than us dropping to 8192.** Our trend-analysis
prompt is ~3,300 tokens with a 4,096-token output budget — about 7,400 of an
8,192 window. We ran at 4096 until 2026-08-05 and it silently truncated every
trend-analysis response (`done_reason: "length"`, zero trends parsed, for
weeks). 8192 would leave us ~800 tokens of headroom, which is close enough to
the cliff that we would rather not.

**Cost to Algora: effectively zero.**

- *Latency after load: unchanged.* Decode cost scales with the tokens actually
  used, not with the window allocated. Your calls are small (we see 19–24
  token completions in `algora-api` logs); at 16384 they still compute only
  those tokens.
- *VRAM: about +0.15 GB.* Measured on this host: gemma3:4b at 4096 = 2.88 GB,
  at 8192 = 3.03 GB. gemma3's sliding-window attention keeps the KV cache
  cheap, so 16384 should land near 3.2 GB — against ~5 GB free.
- *One-time model load: ~60 s*, the figure from your own comment. Today you are
  not paying it and we are paying it on every call; afterwards **neither of us
  pays it**, because we would share one instance.

## Two optional improvements, entirely your call

These are observations, not requests.

1. **Small calls may not need a 4B model.** The completions we see in your logs
   are 19–24 tokens. The host already has `gemma3:1b`, `llama3.2:1b` and
   `qwen3:1.7b` pulled. A smaller model for the `complexity: 'fast'` path would
   free the 4B instance and cut your own latency.
2. **`keep_alive: '15m'` on a call arriving every ~90 s is a permanent hold.**
   That is defensible given a ~60 s cold load — but if item 1 happens, a
   shorter hold would make the host friendlier to share. If we converge on one
   `num_ctx`, this stops mattering at all.

## Contact

Happy to make the change on our side instead, or to coordinate a different
number, if 16384 does not suit you. The one thing that does not work is the two
of us picking different values — whoever loses the race stalls indefinitely.

Verification after the change: `curl -s $OLLAMA/api/ps` should show a single
`gemma3:4b` entry with `context_length: 16384` serving both services.
