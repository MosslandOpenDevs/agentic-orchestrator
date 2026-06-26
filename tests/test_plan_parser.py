"""Tests for PlanParser (project/parser.py).

Previously had zero coverage. PlanParser.parse() is synchronous and regex-based
(no LLM), so it can be exercised end-to-end on a representative plan document.
"""

from agentic_orchestrator.project.parser import PlanParser, TechStack

SAMPLE_PLAN = """# Mossland NFT Valuation Tracker

## Project Overview
A real-time dashboard for tracking Mossland NFT valuations using AI agents.
It serves NFT holders who want live, accurate price data and portfolio insights.

## Technical Architecture
Frontend: Next.js with React. Backend: FastAPI (Python). Database: PostgreSQL.
Blockchain: Ethereum with Solidity smart contracts.

## Features
- Real-time NFT price tracking
- Portfolio valuation dashboard
- Price alerts via webhooks

## Risks
- External API rate limits
- On-chain data latency

## KPIs
- 1000 monthly active users
- 99.9% uptime
"""


class TestParseEndToEnd:
    def setup_method(self):
        self.parser = PlanParser()

    def test_title_from_h1(self):
        parsed = self.parser.parse(SAMPLE_PLAN)
        assert parsed.title == "Mossland NFT Valuation Tracker"

    def test_explicit_title_overrides_extraction(self):
        parsed = self.parser.parse(SAMPLE_PLAN, title="Explicit Title")
        assert parsed.title == "Explicit Title"

    def test_tech_stack_detected(self):
        ts = self.parser.parse(SAMPLE_PLAN).tech_stack
        assert ts.frontend == "nextjs"
        assert ts.backend == "fastapi"
        assert ts.database == "postgresql"
        assert ts.blockchain == "ethereum"
        # react also appears but the primary frontend slot is taken -> additional
        assert "react" in ts.additional

    def test_features_extracted(self):
        features = self.parser.parse(SAMPLE_PLAN).features
        assert len(features) == 3
        assert "Real-time NFT price tracking" in features

    def test_risks_and_kpis(self):
        parsed = self.parser.parse(SAMPLE_PLAN)
        assert len(parsed.risks) == 2
        assert len(parsed.kpis) == 2

    def test_summary_non_empty(self):
        summary = self.parser.parse(SAMPLE_PLAN).summary
        assert "real-time dashboard" in summary.lower()

    def test_raw_content_preserved(self):
        assert self.parser.parse(SAMPLE_PLAN).raw_content == SAMPLE_PLAN


class TestParseEdgeCases:
    def setup_method(self):
        self.parser = PlanParser()

    def test_empty_content_returns_untitled(self):
        parsed = self.parser.parse("")
        assert parsed.title == "Untitled Project"
        assert parsed.features == []
        assert isinstance(parsed.tech_stack, TechStack)

    def test_empty_content_respects_given_title(self):
        assert self.parser.parse("", title="Given").title == "Given"

    def test_title_from_plan_prefix_when_no_h1(self):
        parsed = self.parser.parse("Plan: Decentralized Identity Vault\n\nSome body text here.")
        assert parsed.title == "Decentralized Identity Vault"


class TestTechDetection:
    def setup_method(self):
        self.parser = PlanParser()

    def test_detects_vue_and_django_and_solana(self):
        ts = self.parser._detect_tech_stack(
            "We will use Vue.js on the frontend, Django backend, and the Solana blockchain."
        )
        assert ts.frontend == "vue"
        assert ts.backend == "django"
        assert ts.blockchain == "solana"

    def test_no_tech_leaves_fields_empty(self):
        ts = self.parser._detect_tech_stack("A plan with no concrete technology mentioned at all.")
        assert ts.frontend is None
        assert ts.backend is None
        assert ts.blockchain is None
