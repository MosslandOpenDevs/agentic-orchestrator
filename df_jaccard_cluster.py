"""Document-frequency-filtered Jaccard clustering for debate ideas.

Problem this solves
-------------------
A single multi-stage debate emits ~24 idea titles that are all *distinct
strings* but collapse into ~6-7 genuine themes.  Every title repeats the
debate's topic vocabulary ("x402", "AI", "Agent", "Mossland", "API",
"Cloudflare"), so plain Jaccard over title tokens says everything is similar
to everything, and the production first-N-token prefix fingerprint says
nothing is similar to anything.  The discriminating signal lives in the
*minority* terms (gateway / firewall / refund / sandbox / spend-cap ...).

Approach: down-weight by corpus document frequency, but as a hard filter
rather than a TF-IDF weighting, so the result is still a plain, auditable
Jaccard over a small token set.

    1. tokenize + light deterministic stemming
    2. drop an English stoplist
    3. drop tokens whose corpus DF exceeds a cutoff  (topic vocabulary)
    4. drop tokens whose corpus DF is below min_df   (idiosyncratic phrasing;
       a token in exactly one document can never contribute to any pairwise
       intersection, it can only inflate unions)
    5. Jaccard over what survives, gated by min_shared_terms
    6. single-linkage agglomerative merge, deterministic tie-breaks
    7. plus a raw near-duplicate layer that fires regardless of the DF filter,
       so a homogeneous corpus cannot filter its own theme out of existence

Stdlib only.  O(n^2) similarity, O(n^3) worst-case merging; measured at
3 ms for n=24, 25 ms for n=50, 171 ms for n=100.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "IdeaInput",
    "Cluster",
    "ClusterResult",
    "DFJaccardClusterer",
    "cluster_ideas",
]

# --------------------------------------------------------------------------
# Tokenization
# --------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z0-9]+")
_COMPOUND_RE = re.compile(r"[a-z0-9]+(?:[-/][a-z0-9]+)+")

# Ordinary English function words.  Deliberately small: the DF filter removes
# corpus-specific noise, this list only removes words that are noise in every
# corpus and would otherwise survive in a small document set.
STOPWORDS: FrozenSet[str] = frozenset(
    """
    a an the and or but if then than that this these those with without within
    into onto from for of on in at by to as is are was were be been being am
    it its it's their there here we our you your they them he she his her
    not no nor so such via over under between across through during about
    per each every any all both few more most other some via using use used
    new via can will would should could may might must do does did done
    how what when where which who whom why whose
    """.split()
)

# Korean particles, matching the existing aggregator stoplist.
STOPWORDS = STOPWORDS | frozenset("의 을 를 이 가 은 는 에 와 과".split())

# Bracket tags the pipeline prepends to titles ("[Idea] ...", "[Plan] ...").
_TAG_RE = re.compile(r"^\s*\[[^\]]{0,24}\]\s*")


def _stem(token: str) -> str:
    """Deterministic, conservative plural/gerund folding.

    Not a real stemmer -- just enough to make ``agents``/``agent``,
    ``receipts``/``receipt``, ``royalties``/``royalty`` collide.  Aggressive
    stemming would fuse genuinely different terms, which costs more here than
    a missed match does.
    """
    if len(token) <= 3 or token.isdigit():
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    for suffix in ("sses", "shes", "ches", "xes", "zes"):
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            return token[:-2]
    if token.endswith("s") and not token.endswith(("ss", "us", "is", "as")):
        return token[:-1]
    return token


def tokenize_with_glue(text: str) -> Tuple[List[str], Dict[str, Tuple[str, ...]]]:
    """Lowercase, strip a leading ``[tag]``, split, stem.

    Hyphenated compounds emit their parts *and* the glued form, so
    ``Micro-Payment`` and ``Micropayment`` -- which LLM titles mix freely --
    can still meet.

    Returns the token list plus provenance for every glued form it invented,
    so the caller can later discard glue that turned out to be a redundant
    restatement of one of its own parts (``x402-Backed`` -> ``backed`` +
    ``x402backed``, which would otherwise contribute *two* units of overlap
    for one shared word).
    """
    text = unicodedata.normalize("NFKC", text or "")
    text = _TAG_RE.sub("", text.lower())
    text = text.replace("‐", "-").replace("‑", "-").replace("–", "-")

    out: List[str] = []
    glue: Dict[str, Tuple[str, ...]] = {}
    for compound in _COMPOUND_RE.findall(text):
        glued = _stem(re.sub(r"[-/]", "", compound))
        if len(glued) > 3:
            out.append(glued)
            glue[glued] = tuple(_stem(p) for p in _WORD_RE.findall(compound))
    for word in _WORD_RE.findall(text):
        out.append(_stem(word))
    return out, glue


def tokenize(text: str) -> List[str]:
    """Token list only -- see :func:`tokenize_with_glue`."""
    return tokenize_with_glue(text)[0]


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IdeaInput:
    """One idea to be clustered.  ``content`` is optional."""

    key: str
    title: str
    content: str = ""


@dataclass
class Cluster:
    """A theme.  ``representative`` is the key of the chosen exemplar."""

    cluster_id: int
    representative: str
    member_keys: Tuple[str, ...]
    shared_terms: Tuple[str, ...]
    cohesion: float  # mean pairwise similarity inside the cluster (1.0 if size 1)

    @property
    def size(self) -> int:
        return len(self.member_keys)


@dataclass
class ClusterResult:
    clusters: List[Cluster]
    #: tokens removed as corpus topic vocabulary, with their DF
    dropped_high_df: Tuple[Tuple[str, int], ...] = ()
    #: per-idea surviving discriminating token set, for debugging
    signatures: Dict[str, Tuple[str, ...]] = field(default_factory=dict)
    #: fraction of the raw vocabulary that survived filtering.  Health signal:
    #: when one theme dominates the corpus its defining words look like topic
    #: vocabulary and are deleted, and this number collapses.  A run with a low
    #: retention AND no multi-member clusters is the degenerate case, not a
    #: genuinely diverse debate -- alarm on it rather than trusting the output.
    vocabulary_retained: float = 1.0

    @property
    def n_clusters(self) -> int:
        return len(self.clusters)


# --------------------------------------------------------------------------
# Clusterer
# --------------------------------------------------------------------------


class DFJaccardClusterer:
    """Cluster ideas by Jaccard over document-frequency-filtered tokens.

    Parameters
    ----------
    threshold:
        Merge cutoff on the [0, 1] similarity.  Recommended 0.30.
    max_df_ratio:
        Tokens appearing in more than this fraction of documents are treated
        as topic vocabulary and dropped.
    max_df_floor:
        A token is never dropped as "too common" unless it appears in at least
        this many documents.  Protects tiny corpora, where *every* token looks
        frequent (with n=3, one shared word is already 33%).
    min_df:
        Tokens appearing in fewer than this many documents are dropped.  A
        DF-1 token cannot appear in any intersection, so it only inflates
        unions and pushes every pair apart by an amount that depends on how
        verbose each title happens to be.
    min_df_corpus_size:
        ``min_df`` is only applied once the corpus is at least this large.
        Below it, DF-1 pruning would erase the entire difference between two
        documents and merge them at similarity 1.0.
    min_shared_terms:
        A pair must share at least this many discriminating terms to be
        eligible to merge.  This is what makes the threshold safe rather than
        magic: without it, a single accidental token collision seeds a chain
        and the whole corpus fuses into one cluster once ``threshold`` drops
        below ~0.25 (measured: 24 ideas -> 1 cluster at 0.15).  With it, the
        same sweep bottoms out at 9 clusters.
    content_weight:
        Blend weight for a second Jaccard computed over the optional content
        field: ``sim = (1 - w) * sim_title + w * sim_content``.  0.0 disables
        content entirely (recommended -- measured, content only ever split
        clusters further: F1 0.79 at w=0 vs 0.56 at w=0.3 vs 0.00 at w=1.0,
        because 600-char bodies share long generic tails).
    linkage:
        ``"single"`` (default) or ``"average"``.  A theme is a *chain* of
        related phrasings, not a ball -- "marketplace/metering" and
        "paywall/micro-payment" are the same theme but share no token, and
        only meet through intermediate titles.  Average linkage cannot express
        that and over-splits (measured: 15 clusters vs 11 at threshold 0.30).
        Single linkage's chaining risk is contained by ``min_shared_terms``.
    prune_redundant_glue:
        Drop a hyphen-glue token that covers no document its own parts did not
        already cover.  Without it, "x402-Backed" contributes both ``backed``
        and ``x402backed`` and one shared word counts twice.
    near_duplicate_threshold:
        Raw-token (stoplist-only, no DF filtering) Jaccard above which a pair
        is always merged.  Set to a value > 1.0 to disable.  This exists for
        the homogeneous-corpus regime -- see the comment in ``cluster``.
    """

    def __init__(
        self,
        threshold: float = 0.30,
        max_df_ratio: float = 0.30,
        max_df_floor: int = 3,
        min_df: int = 2,
        min_df_corpus_size: int = 5,
        min_shared_terms: int = 2,
        content_weight: float = 0.0,
        linkage: str = "single",
        prune_redundant_glue: bool = True,
        near_duplicate_threshold: float = 0.75,
    ) -> None:
        if not 0.0 < threshold <= 1.0:
            raise ValueError("threshold must be in (0, 1]")
        if linkage not in ("average", "single"):
            raise ValueError("linkage must be 'average' or 'single'")
        self.threshold = threshold
        self.max_df_ratio = max_df_ratio
        self.max_df_floor = max_df_floor
        self.min_df = min_df
        self.min_df_corpus_size = min_df_corpus_size
        self.min_shared_terms = min_shared_terms
        self.content_weight = content_weight
        self.linkage = linkage
        self.prune_redundant_glue = prune_redundant_glue
        self.near_duplicate_threshold = near_duplicate_threshold

    # -- token sets ------------------------------------------------------

    @staticmethod
    def _token_sets(
        texts: Sequence[str],
    ) -> Tuple[List[FrozenSet[str]], Dict[str, Tuple[str, ...]]]:
        sets: List[FrozenSet[str]] = []
        glue: Dict[str, Tuple[str, ...]] = {}
        for text in texts:
            toks, g = tokenize_with_glue(text)
            sets.append(frozenset(toks) - STOPWORDS)
            for k, v in g.items():
                glue.setdefault(k, v)
        return sets, glue

    # -- vocabulary ------------------------------------------------------

    def _document_frequency(self, docs: Sequence[FrozenSet[str]]) -> Dict[str, int]:
        df: Dict[str, int] = {}
        for tokens in docs:
            for tok in tokens:
                df[tok] = df.get(tok, 0) + 1
        return df

    def _filter_vocab(
        self,
        docs: Sequence[FrozenSet[str]],
        glue: Optional[Dict[str, Tuple[str, ...]]] = None,
    ) -> Tuple[List[FrozenSet[str]], List[Tuple[str, int]]]:
        n = len(docs)
        df = self._document_frequency(docs)
        high_cut = max(self.max_df_floor, math.ceil(self.max_df_ratio * n))
        apply_min_df = n >= self.min_df_corpus_size

        keep = set()
        dropped_high: List[Tuple[str, int]] = []
        for tok, count in df.items():
            if count > high_cut:
                dropped_high.append((tok, count))
                continue
            if apply_min_df and count < self.min_df:
                continue
            keep.add(tok)

        if glue and self.prune_redundant_glue:
            # Discard a glued compound that adds no document its own parts did
            # not already cover.  "x402-Backed" invents `x402backed`, whose
            # posting list is identical to `backed`'s -- keeping both makes one
            # shared word contribute two units of overlap.  It also smuggles a
            # dropped topic word back in under an alias (`x402powered` is a
            # subset of `x402`, which the DF filter just removed).  A glue form
            # that genuinely bridges spellings -- `micropayment`, which unifies
            # "Micro-Payment" with "Micropayments" -- covers documents no part
            # covers alone and survives.
            postings: Dict[str, set] = {}
            for idx, toks in enumerate(docs):
                for tok in toks:
                    postings.setdefault(tok, set()).add(idx)
            for glued in sorted(glue):
                if glued not in keep:
                    continue
                own = postings.get(glued, set())
                for part in glue[glued]:
                    if part != glued and own <= postings.get(part, set()):
                        keep.discard(glued)
                        break

        dropped_high.sort(key=lambda kv: (-kv[1], kv[0]))
        return [frozenset(toks & keep) for toks in docs], dropped_high

    # -- similarity ------------------------------------------------------

    @staticmethod
    def _jaccard(a: FrozenSet[str], b: FrozenSet[str]) -> Tuple[float, int]:
        if not a or not b:
            return 0.0, 0
        inter = len(a & b)
        if inter == 0:
            return 0.0, 0
        return inter / len(a | b), inter

    # -- clustering ------------------------------------------------------

    def cluster(self, ideas: Sequence[IdeaInput]) -> ClusterResult:
        ideas = list(ideas)
        n = len(ideas)
        if n == 0:
            return ClusterResult(clusters=[])
        if n == 1:
            return ClusterResult(
                clusters=[
                    Cluster(0, ideas[0].key, (ideas[0].key,), (), 1.0)
                ],
                signatures={ideas[0].key: ()},
            )

        title_raw, title_glue = self._token_sets([i.title for i in ideas])
        title_sets, dropped_high = self._filter_vocab(title_raw, title_glue)

        use_content = self.content_weight > 0.0 and any(i.content for i in ideas)
        if use_content:
            content_raw, content_glue = self._token_sets([i.content for i in ideas])
            content_sets, _ = self._filter_vocab(content_raw, content_glue)
        else:
            content_sets = [frozenset()] * n

        # Pairwise similarity, upper triangle only.
        #
        # Two layers, because the DF filter has one degenerate regime: when a
        # corpus is homogeneous, the very words that define the shared theme
        # have DF near 1.0 and get deleted as "topic vocabulary", leaving every
        # document with an empty signature.  24 copies of one title would come
        # back as 24 singletons -- the exact inverse of the desired answer.
        # So a pair that is a near-copy in *raw* text (stoplist only, no DF
        # filtering) is always joined, whatever the corpus looks like.  On a
        # normally varied debate this layer is inert: the golden 24 top out at
        # 0.462 raw similarity, far under the 0.75 gate.
        sim: Dict[Tuple[int, int], float] = {}
        for i in range(n):
            for j in range(i + 1, n):
                raw_s, _ = self._jaccard(title_raw[i], title_raw[j])
                if raw_s >= self.near_duplicate_threshold:
                    sim[(i, j)] = 1.0
                    continue
                s_t, shared = self._jaccard(title_sets[i], title_sets[j])
                if shared < self.min_shared_terms:
                    continue
                if use_content:
                    s_c, _ = self._jaccard(content_sets[i], content_sets[j])
                    s = (1.0 - self.content_weight) * s_t + self.content_weight * s_c
                else:
                    s = s_t
                if s > 0.0:
                    sim[(i, j)] = s

        def pair_sim(a: int, b: int) -> float:
            return sim.get((a, b) if a < b else (b, a), 0.0)

        # Agglomerative merge.  Clusters are kept as sorted index tuples and
        # always identified by their smallest member, so the whole procedure
        # is a pure function of the input ordering -- no dict iteration order
        # and no set iteration order leaks into the result.
        groups: List[List[int]] = [[i] for i in range(n)]

        while True:
            best: Optional[Tuple[float, int, int]] = None
            for gi in range(len(groups)):
                for gj in range(gi + 1, len(groups)):
                    a, b = groups[gi], groups[gj]
                    if self.linkage == "single":
                        score = max(pair_sim(x, y) for x in a for y in b)
                    else:
                        score = sum(pair_sim(x, y) for x in a for y in b) / (
                            len(a) * len(b)
                        )
                    if score < self.threshold:
                        continue
                    # Tie-break on the lowest (gi, gj) so equal scores always
                    # resolve the same way.
                    if best is None or score > best[0] + 1e-12:
                        best = (score, gi, gj)
            if best is None:
                break
            _, gi, gj = best
            merged = sorted(groups[gi] + groups[gj])
            groups = [g for k, g in enumerate(groups) if k not in (gi, gj)]
            groups.append(merged)
            groups.sort(key=lambda g: g[0])

        clusters: List[Cluster] = []
        for cid, members in enumerate(sorted(groups, key=lambda g: (-len(g), g[0]))):
            rep = self._pick_representative(members, ideas, title_sets, pair_sim)
            shared = frozenset.intersection(*[title_sets[m] for m in members])
            if len(members) > 1:
                pairs = [
                    pair_sim(members[x], members[y])
                    for x in range(len(members))
                    for y in range(x + 1, len(members))
                ]
                cohesion = sum(pairs) / len(pairs)
            else:
                cohesion = 1.0
            clusters.append(
                Cluster(
                    cluster_id=cid,
                    representative=ideas[rep].key,
                    member_keys=tuple(ideas[m].key for m in members),
                    shared_terms=tuple(sorted(shared)),
                    cohesion=round(cohesion, 4),
                )
            )

        raw_vocab = set().union(*title_raw) if title_raw else set()
        kept_vocab = set().union(*title_sets) if title_sets else set()
        return ClusterResult(
            clusters=clusters,
            dropped_high_df=tuple(dropped_high),
            signatures={
                ideas[i].key: tuple(sorted(title_sets[i])) for i in range(n)
            },
            vocabulary_retained=(
                round(len(kept_vocab) / len(raw_vocab), 4) if raw_vocab else 1.0
            ),
        )

    # -- representative --------------------------------------------------

    def _pick_representative(
        self,
        members: Sequence[int],
        ideas: Sequence[IdeaInput],
        title_sets: Sequence[FrozenSet[str]],
        pair_sim,
    ) -> int:
        """Medoid: the member most similar to the rest of its own cluster.

        Rationale -- scoring has not run yet, so quality signals are not
        available; the only information present is the cluster's own
        vocabulary.  The medoid is the phrasing that best covers the terms the
        cluster agrees on, i.e. the least idiosyncratic statement of the
        theme.  A "longest title" or "first proposed" rule would instead pick
        whichever agent was most verbose or happened to speak first.

        Ties (common at size 2, where every member has identical centrality)
        fall through to: more discriminating terms -> longer title (the
        repo's 30+ char specificity rule) -> input order.
        """
        best_idx = members[0]
        best_key: Optional[Tuple[float, int, int, int]] = None
        for m in members:
            centrality = sum(pair_sim(m, o) for o in members if o != m)
            rank = (
                centrality,
                len(title_sets[m]),
                len(ideas[m].title),
                -m,  # earlier input position wins the final tie
            )
            if best_key is None or rank > best_key:
                best_key = rank
                best_idx = m
        return best_idx


def cluster_ideas(
    ideas: Iterable[IdeaInput], threshold: float = 0.30, **kwargs
) -> ClusterResult:
    """Convenience wrapper."""
    return DFJaccardClusterer(threshold=threshold, **kwargs).cluster(list(ideas))
