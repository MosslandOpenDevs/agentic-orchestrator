"""Deterministic TF-IDF cosine clustering for debate ideas (stdlib only).

Problem this solves: one multi-agent debate emits ~24 idea titles that are all
*distinct strings* but collapse into ~6-7 themes. The old dedup (first-N-token
prefix fingerprint) catches none of them, so three same-theme ideas can each be
promoted and each scaffold a near-identical project.

Design in one line: hand-rolled TF-IDF vectors (collections.Counter + math),
cosine similarity, then greedy max-degree "star" clustering where every member
must be within threshold of the *representative itself* (not single-linkage,
so themes cannot chain into one blob).

No numpy, no sklearn, no network, no LLM. O(n^2) similarity, O(n^3) worst-case
clustering, which is nothing at n <= 50.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Sequence

__all__ = ["IdeaDoc", "Cluster", "ClusterConfig", "cluster_ideas"]

# --------------------------------------------------------------------------
# Tokenisation
# --------------------------------------------------------------------------

# Minimal English function-word list. IDF already flattens corpus-wide terms,
# but IDF is *degenerate on tiny corpora* (n=2 -> every df == n -> every weight
# hits the floor), and this list is what keeps small inputs sane.
_STOPWORDS = frozenset("""
    a an the and or but for nor so yet of to in on at by with from into onto
    over under as is are was were be been being am do does did done doing
    it its this that these those there here their his her our your my
    not no if then than when while where which who whom whose what how why
    can could should would may might must will shall each every both all any
    some via per about across after before between during through within
    """.split())

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _singularise(tok: str) -> str:
    """Conservative plural stripping. Deliberately not a real stemmer.

    Merges agent/agents, receipt/receipts, sandbox/sandboxes, registry/
    registries. Does NOT touch -ed/-ing: those rules mangle far more real
    tokens than they merge, and the cost of a wrong merge here is a wrong
    cluster.
    """
    if len(tok) <= 3 or tok.isdigit():
        return tok
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith(("sses", "shes", "ches", "xes", "zes")):
        return tok[:-2]
    if tok.endswith("s") and not tok.endswith(("ss", "us", "is", "as", "os")):
        return tok[:-1]
    return tok


def tokenize(text: str | None) -> list[str]:
    """lowercase -> split on non-alphanumerics -> stopword drop -> singularise.

    Splitting on non-alphanumerics is load-bearing: it turns "x402-Powered"
    into ("x402", "powered") and "Micro-Payment" into ("micro", "payment"),
    which is what lets the minority terms line up across differently
    hyphenated titles. "x402" survives intact because it is already alnum.
    """
    if not text:
        return []
    out: list[str] = []
    for raw in _SPLIT_RE.split(text.lower()):
        if not raw or len(raw) < 2 or raw in _STOPWORDS:
            continue
        for tok in _TOKEN_RE.findall(raw):
            tok = _singularise(tok)
            if len(tok) >= 2 and tok not in _STOPWORDS:
                out.append(tok)
    return out


# --------------------------------------------------------------------------
# Vector space
# --------------------------------------------------------------------------

# Floor keeps a corpus-universal term at a tiny-but-nonzero weight. Without it,
# idf == 0.0 for every term of two identical documents (df == n for all terms),
# both vectors become the zero vector, cosine is 0/0, and the single most
# obvious duplicate case in the world fails open.
_IDF_FLOOR = 0.01

# Below this many documents, df carries no information (with 2 docs every term
# is either df=1 or df=2) so hard df-stopwording is switched off and only the
# soft IDF weighting applies.
_MIN_DOCS_FOR_DF_STOPWORDING = 6

# Defaults measured on tests/data/golden_debate_x402.json (24 ideas, 7 themes):
# k=11, pairwise precision 1.00, recall 0.79, F1 0.88 against a hand label.
# Chosen to favour precision: wrongly merging two real themes silently deletes
# an idea, wrongly splitting one only costs a duplicate that later stages see.
DEFAULT_THRESHOLD = 0.18
DEFAULT_CONTENT_WEIGHT = 0.5
DEFAULT_MAX_DF_RATIO = 0.6

# Two documents must share at least this many discriminating (post-IDF) terms
# before any similarity is credited. Without it the design is safe only
# because the default threshold happens to be high: measured on a corpus of
# 24 unrelated domains, dropping the threshold to 0.04-0.08 collapsed it to
# 15-17 clusters (largest = 5 unrelated ideas), i.e. a well-meaning "let's
# dedup a bit harder" config edit would silently destroy real ideas. With the
# guard the same sweep returns 24/24 singletons at every threshold measured.
DEFAULT_MIN_SHARED_TERMS = 2


def _idf_table(token_sets: Sequence[Iterable[str]], max_df_ratio: float = 1.0) -> dict[str, float]:
    """Smoothed IDF: ln((n+1)/(df+1)), floored at _IDF_FLOOR.

    This is the answer to the shared-topic-vocabulary problem. On the x402
    corpus "x402"/"agent"/"ai" appear in ~every title and land at ~0.0-0.04,
    while "escrow"/"sandbox"/"refund" appear 2-4 times and land at ~1.6-2.5.
    The down-weighting is *learned from the corpus*, so the same code works on
    an NFT or DAO-governance debate with a completely different shared
    vocabulary - nothing topical is hard-coded.

    `max_df_ratio` adds hard document-frequency stopwording on top: a term in
    more than that fraction of documents is dropped outright rather than just
    down-weighted. Soft IDF alone is not enough here, because cosine
    normalisation means a dozen near-zero shared terms still inflate both
    vectors' norms and dilute the one term that actually carries the theme.
    Only applied when the corpus is big enough for df to mean anything.
    """
    n = len(token_sets)
    df: Counter[str] = Counter()
    for toks in token_sets:
        df.update(set(toks))
    cutoff = n + 1
    if n >= _MIN_DOCS_FOR_DF_STOPWORDING and 0.0 < max_df_ratio < 1.0:
        cutoff = max(2, math.ceil(max_df_ratio * n))
    return {
        term: max(_IDF_FLOOR, math.log((n + 1) / (count + 1)))
        for term, count in df.items()
        if count < cutoff
    }


def _weighted_unit_vector(tokens: Sequence[str], idf: dict[str, float]) -> dict[str, float]:
    """Sublinear-tf * idf, L2-normalised. Empty input -> empty vector.

    A term absent from `idf` was df-stopworded away and contributes nothing -
    not even to the norm. That is the whole point of the hard cutoff.
    """
    if not tokens:
        return {}
    tf = Counter(tokens)
    vec = {term: (1.0 + math.log(count)) * idf[term] for term, count in tf.items() if term in idf}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0.0:
        return {}
    return {term: v / norm for term, v in vec.items()}


def _blend(
    title_vec: dict[str, float], content_vec: dict[str, float], content_weight: float
) -> dict[str, float]:
    """Unit(title) + w * Unit(content), re-normalised.

    Both halves are unit-normalised *before* mixing, so `content_weight` is a
    true mixing knob and not an accident of how long the content happens to
    be. Content bodies here are ~1200 chars vs ~80-char titles; blending raw
    counts would silently make this content-only clustering.
    """
    if content_weight <= 0.0 or not content_vec:
        return dict(title_vec)
    merged: dict[str, float] = dict(title_vec)
    for term, val in content_vec.items():
        merged[term] = merged.get(term, 0.0) + content_weight * val
    norm = math.sqrt(sum(v * v for v in merged.values()))
    if norm == 0.0:
        return {}
    return {term: v / norm for term, v in merged.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Both vectors are already unit length, so the dot product is the cosine."""
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(val * b.get(term, 0.0) for term, val in sorted(a.items()))


# --------------------------------------------------------------------------
# Public types
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IdeaDoc:
    """One idea. `content` is optional (core_analysis + proposal, etc.)."""

    key: str
    title: str
    content: str = ""


@dataclass(frozen=True)
class ClusterConfig:
    """Tuned on tests/data/golden_debate_x402.json. See module docstring."""

    threshold: float = DEFAULT_THRESHOLD
    content_weight: float = DEFAULT_CONTENT_WEIGHT
    max_df_ratio: float = DEFAULT_MAX_DF_RATIO
    min_shared_terms: int = DEFAULT_MIN_SHARED_TERMS


@dataclass
class Cluster:
    representative: IdeaDoc
    members: list[IdeaDoc] = field(default_factory=list)
    similarities: list[float] = field(default_factory=list)  # member -> rep
    top_terms: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.members)


# --------------------------------------------------------------------------
# Clustering
# --------------------------------------------------------------------------


def cluster_ideas(
    ideas: Sequence[IdeaDoc],
    threshold: float = DEFAULT_THRESHOLD,
    content_weight: float = DEFAULT_CONTENT_WEIGHT,
    max_df_ratio: float = DEFAULT_MAX_DF_RATIO,
    min_shared_terms: int = DEFAULT_MIN_SHARED_TERMS,
    config: ClusterConfig | None = None,
) -> list[Cluster]:
    """Group near-duplicate ideas; return clusters each with one representative.

    Algorithm (greedy star / dominating-set cover):
      1. Build TF-IDF unit vectors, blend title+content, cosine matrix.
      2. Repeat until every idea is assigned:
           a. Among unassigned ideas, pick the seed with the most unassigned
              neighbours at >= threshold (its *degree*).
           b. Tie-break: total similarity mass -> IDF specificity of its own
              title -> input order. All deterministic.
           c. That seed becomes the representative; absorb every unassigned
              idea within threshold of it.

    Why max-degree seeding is the right representative and not just a
    convenient one: the seed is by construction the densest point of its own
    theme, i.e. the idea that is *most like the other ideas in the theme* -
    a medoid, computed for free by the same pass that forms the cluster. It
    needs no LLM score, which matters because clustering runs before scoring.

    Why star and not agglomerative single-linkage: every member is within
    threshold of the representative *directly*, so cluster diameter is
    bounded. Single-linkage on this corpus chains A->C->B through shared
    boundary terms and collapses the whole debate into one cluster.
    """
    if config is not None:
        threshold = config.threshold
        content_weight = config.content_weight
        max_df_ratio = config.max_df_ratio
        min_shared_terms = config.min_shared_terms

    n = len(ideas)
    if n == 0:
        return []
    if n == 1:
        only = ideas[0]
        return [
            Cluster(
                representative=only,
                members=[only],
                similarities=[1.0],
                top_terms=_top_terms(tokenize(only.title), {}),
            )
        ]

    title_tokens = [tokenize(idea.title) for idea in ideas]
    content_tokens = (
        [tokenize(idea.content) for idea in ideas] if content_weight > 0.0 else [[] for _ in ideas]
    )

    # Separate IDF tables per field, so content_weight=0.0 is bit-identical to
    # a title-only run and content vocabulary never leaks into title weights.
    title_idf = _idf_table(title_tokens, max_df_ratio)
    content_idf = _idf_table(content_tokens, max_df_ratio) if content_weight > 0.0 else {}

    vectors = [
        _blend(
            _weighted_unit_vector(title_tokens[i], title_idf),
            _weighted_unit_vector(content_tokens[i], content_idf),
            content_weight,
        )
        for i in range(n)
    ]

    # Degenerate corpus guard: if every vector came out empty (all titles empty
    # or all-stopword), fall back to exact normalised-string identity so the
    # caller still gets sane groups instead of n singletons or one blob.
    sim = [[0.0] * n for _ in range(n)]
    for i in range(n):
        sim[i][i] = 1.0
        for j in range(i + 1, n):
            if vectors[i] and vectors[j]:
                shared = vectors[i].keys() & vectors[j].keys()
                # A single coincidental shared term is not evidence of the
                # same idea; requiring two keeps unrelated ideas apart even
                # if the threshold is later lowered.
                s = _cosine(vectors[i], vectors[j]) if len(shared) >= min_shared_terms else 0.0
            else:
                s = 1.0 if ideas[i].title.strip().lower() == ideas[j].title.strip().lower() else 0.0
            sim[i][j] = sim[j][i] = s

    # Specificity = total IDF mass of the title. Used only as a tie-break:
    # between two equally central candidates prefer the more informative
    # ("Tokenized Review Escrow for Content QA" over "x402 for AI Agents").
    specificity = [
        sum(title_idf[t] for t in set(title_tokens[i]) if t in title_idf) for i in range(n)
    ]

    unassigned = set(range(n))
    clusters: list[tuple[int, Cluster]] = []

    while unassigned:
        best: tuple[int, float, float, int] | None = None
        best_idx = -1
        for i in sorted(unassigned):  # sorted() -> no set-iteration-order dependence
            degree = 0
            mass = 0.0
            for j in unassigned:
                if j == i:
                    continue
                if sim[i][j] >= threshold:
                    degree += 1
                    mass += sim[i][j]
            # Negative index in the key makes the lowest input index win ties.
            candidate = (degree, mass, specificity[i], -i)
            if best is None or candidate > best:
                best = candidate
                best_idx = i

        seed = best_idx
        members = [seed] + sorted(j for j in unassigned if j != seed and sim[seed][j] >= threshold)
        for j in members:
            unassigned.discard(j)

        clusters.append(
            (
                seed,
                Cluster(
                    representative=ideas[seed],
                    members=[ideas[j] for j in members],
                    similarities=[sim[seed][j] for j in members],
                    top_terms=_top_terms([t for j in members for t in title_tokens[j]], title_idf),
                ),
            )
        )

    # Stable presentation order: biggest theme first, then input order of the
    # representative. Keyed on the seed *index*, not id(), because callers are
    # free to pass the same IdeaDoc object twice.
    clusters.sort(key=lambda pair: (-pair[1].size, pair[0]))
    return [c for _, c in clusters]


def _top_terms(tokens: Sequence[str], idf: dict[str, float], k: int = 5) -> list[str]:
    """Highest IDF-mass terms in a cluster - a cheap human-readable label."""
    if not tokens:
        return []
    tf = Counter(tokens)
    scored = sorted(
        ((term, count * idf.get(term, _IDF_FLOOR)) for term, count in tf.items()),
        key=lambda kv: (-kv[1], kv[0]),
    )
    return [term for term, weight in scored[:k] if weight > 0.05]
