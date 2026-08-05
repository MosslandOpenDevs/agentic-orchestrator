"""Tests for the debate idea diversity gate (v0.6.20).

On 2026-08-05 one debate emitted 24 ideas of which 8 were the same payment
gateway in 8 wordings. All 24 title strings were distinct, so the 6-token
prefix fingerprint caught none of them; three same-theme ideas were each
promoted and each scaffolded a project whose plan document was
byte-identical (16,453 chars) to the others.

The gate clusters a debate's ideas and lets only one representative per
cluster proceed. These tests pin the two properties that matter, in this
order:

1. PRECISION over recall. A merged idea is deleted for good — only the
   representative proceeds — while an unmerged one costs a duplicate, which
   is visible and fixable. So "never merge unrelated ideas" is the hard
   requirement and "merge every duplicate" is the soft one. Tuning to a
   target cluster COUNT is specifically what these tests forbid: on the
   golden data the eyeball answer of 6-7 themes is reachable, but only by
   merging distinct themes.
2. Determinism, and sane behavior on degenerate batches.
"""

import json
from pathlib import Path

import pytest

from agentic_orchestrator.scheduler.idea_clustering import (
    DEFAULT_THRESHOLD,
    IdeaDoc,
    cluster_ideas,
)

GOLDEN_PATH = Path(__file__).parent / "data" / "golden_debate_x402.json"

# Genuinely unrelated ideas — nothing here shares a theme with anything else,
# so any merge among them is a false positive by construction.
DIVERSE_TITLES = [
    "NFT Ticketing for Mossland Metaverse Concerts with Anti-Scalping Resale Caps",
    "DAO Treasury Diversification Policy Engine with Automated Rebalancing",
    "Metaverse Land Price Oracle Using Comparable-Sales Regression",
    "Rooftop Solar Yield Forecasting for Community Energy Cooperatives",
    "Sourdough Starter Health Tracker with Computer Vision Rise Detection",
    "Forklift Battery Swap Scheduling for Warehouse Fleet Uptime",
    "Coral Bleaching Early Warning from Satellite Sea-Surface Temperature",
    "COBOL Dependency Visualizer for Mainframe Migration Planning",
]


@pytest.fixture(scope="module")
def golden():
    data = json.loads(GOLDEN_PATH.read_text())
    return [
        IdeaDoc(
            key=str(i),
            title=item["title"],
            content=f"{item.get('core_analysis', '')} {item.get('proposal', '')}",
        )
        for i, item in enumerate(data)
    ]


def diverse_docs(prefix="d"):
    return [IdeaDoc(key=f"{prefix}{i}", title=t) for i, t in enumerate(DIVERSE_TITLES)]


class TestGoldenReplay:
    """Replay the debate that caused the incident, with no external effects."""

    def test_the_incident_cluster_collapses_to_one_representative(self, golden):
        # The 8 gateway/marketplace/paywall titles are the ones that produced
        # three identical projects. Exactly one of them may proceed.
        clusters = cluster_ideas(golden)
        gateway_keywords = ("marketplace", "paywall", "gateway", "exchange")

        def is_gateway(doc):
            low = doc.title.lower()
            return any(k in low for k in gateway_keywords)

        gateway_reps = [c for c in clusters if is_gateway(c.representative)]
        assert len(gateway_reps) == 1, (
            "the payment-gateway theme must survive as ONE representative; "
            f"got {[c.representative.title for c in gateway_reps]}"
        )
        assert gateway_reps[0].size >= 6  # absorbs the near-duplicates

    def test_gate_reduces_the_batch_but_keeps_most_themes(self, golden):
        clusters = cluster_ideas(golden)
        # Fewer externalized ideas than the 24 that caused the flood...
        assert len(clusters) < len(golden)
        # ...but nowhere near the 6-7 an eyeball count suggests: reaching
        # that requires merging distinct themes. This asserts a floor, not a
        # target — see the module docstring.
        assert len(clusters) >= 9

    def test_every_idea_is_accounted_for_exactly_once(self, golden):
        clusters = cluster_ideas(golden)
        keys = [m.key for c in clusters for m in c.members]
        assert sorted(keys, key=int) == [d.key for d in golden]
        assert len(keys) == len(set(keys))

    def test_representative_belongs_to_its_own_cluster(self, golden):
        for cluster in cluster_ideas(golden):
            assert cluster.representative in cluster.members


class TestPrecisionGuards:
    """The dangerous failure is a merge, not a miss."""

    def test_unrelated_ideas_are_never_merged(self):
        clusters = cluster_ideas(diverse_docs())
        assert len(clusters) == len(DIVERSE_TITLES)

    def test_unrelated_ideas_survive_an_aggressively_low_threshold(self):
        # This is what min_shared_terms buys. Without the guard, a
        # well-meaning "let's dedup harder" config edit collapses unrelated
        # ideas; with it, the batch is stable all the way down.
        for threshold in (0.02, 0.04, 0.08, 0.12):
            clusters = cluster_ideas(diverse_docs(), threshold=threshold)
            assert len(clusters) == len(DIVERSE_TITLES), (
                f"threshold {threshold} merged unrelated ideas: "
                f"{[[m.title[:30] for m in c.members] for c in clusters if c.size > 1]}"
            )

    def test_intruders_are_not_absorbed_into_the_golden_themes(self, golden):
        mixed = list(golden) + diverse_docs(prefix="x")
        clusters = cluster_ideas(mixed)
        contaminated = [
            c
            for c in clusters
            if c.size > 1 and any(m.key.startswith("x") for m in c.members)
        ]
        assert contaminated == []


class TestDegenerateBatches:
    @pytest.mark.parametrize(
        "titles,expected",
        [
            ([], 0),
            (["Only One Idea About Agent Payment Rails"], 1),
            (["Identical Title Here", "Identical Title Here"], 1),
            (["NFT Ticketing Platform", "Rooftop Solar Forecasting"], 2),
        ],
    )
    def test_small_batches_do_not_raise_or_collapse(self, titles, expected):
        docs = [IdeaDoc(key=str(i), title=t) for i, t in enumerate(titles)]
        assert len(cluster_ideas(docs)) == expected

    def test_empty_titles_do_not_explode(self):
        docs = [IdeaDoc(key="a", title=""), IdeaDoc(key="b", title="")]
        assert len(cluster_ideas(docs)) >= 1


class TestDeterminism:
    def test_same_input_same_output(self, golden):
        first = cluster_ideas(golden)
        second = cluster_ideas(golden)
        assert [c.representative.key for c in first] == [
            c.representative.key for c in second
        ]
        assert [sorted(m.key for m in c.members) for c in first] == [
            sorted(m.key for m in c.members) for c in second
        ]

    def test_threshold_default_matches_the_measured_recommendation(self):
        # 0.18 is the lowest threshold reaching pairwise precision 1.00 on the
        # golden data. If someone lowers this, the precision tests above are
        # what should stop them.
        assert DEFAULT_THRESHOLD == 0.18
