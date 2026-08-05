"""
Trend analysis using LLM.

Analyzes feed items to identify trending topics using local LLM (Ollama).
"""

import json
import re
from typing import Optional

from ..llm.router import HybridLLMRouter
from ..timeutil import utcnow
from ..utils.config import Config, load_config
from ..utils.logging import get_logger
from .models import FeedItem, Trend, TrendAnalysis

logger = get_logger(__name__)


class TrendAnalyzer:
    """
    Analyzes feed items to identify trending topics.

    Uses local LLM (Ollama) via HybridLLMRouter to extract and score trends.
    """

    # Maximum articles to include in a single analysis prompt
    # Cap signals fed into the LLM. With ~100 items, prompts hit ~13k chars
    # and gemma3:4b/:9b regularly miss the 600 s Ollama timeout. 50 keeps
    # prompts around ~6 k chars and lets the small model finish in 1-2 min.
    MAX_ARTICLES_PER_ANALYSIS = 50

    # System message for trend analysis
    SYSTEM_MESSAGE = """You are an expert trend analyst specializing in technology,
cryptocurrency, and Web3 industries. Your task is to identify the most significant
trending topics from news headlines and summaries.

Focus on:
1. Topics that appear across multiple sources
2. Emerging technologies and protocols
3. Market-moving events and announcements
4. Regulatory developments
5. Major product launches or updates

Prioritize trends with:
- High relevance to Web3/blockchain ecosystem
- Potential for building micro-services or tools
- Clear user needs or pain points
- Technical feasibility for small teams"""

    # JSON schema enforced by Ollama structured outputs (the `format` field,
    # grammar-constrained decoding). With this in place the model cannot emit
    # the failure shapes the lenient parser exists for — smart-quote
    # delimiters, prose preambles, markdown fences. The parser stays as
    # defense in depth: schema-valid is not semantically-valid, and a
    # max_tokens truncation can still cut the document short.
    #
    # `required` lists only the fields the parser has no default for;
    # article_count/sources/sample_headlines degrade gracefully when absent.
    TRENDS_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "trends": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "score": {"type": "number"},
                        "sources": {"type": "array", "items": {"type": "string"}},
                        "article_count": {"type": "integer"},
                        "sample_headlines": {"type": "array", "items": {"type": "string"}},
                        "category": {"type": "string"},
                        "summary": {"type": "string"},
                        "web3_relevance": {"type": "string"},
                        "idea_seeds": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["topic", "keywords", "score", "category", "summary"],
                },
            },
        },
        "required": ["trends"],
    }

    def __init__(
        self,
        router: Optional[HybridLLMRouter] = None,
        config: Config | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize trend analyzer.

        Args:
            router: HybridLLMRouter for LLM analysis (uses local Ollama).
            config: Configuration object.
            dry_run: If True, skip LLM calls and return mock data.
        """
        self._router = router
        self.config = config or load_config()
        self.dry_run = dry_run

    @property
    def router(self) -> HybridLLMRouter:
        """Lazy-loaded HybridLLMRouter."""
        if self._router is None:
            self._router = HybridLLMRouter()
        return self._router

    async def analyze_trends(
        self,
        items: list[FeedItem],
        period: str,
        max_trends: int = 10,
    ) -> TrendAnalysis:
        """
        Analyze feed items to identify trends.

        Args:
            items: List of feed items to analyze.
            period: Time period being analyzed (24h, 1w, 1m).
            max_trends: Maximum number of trends to identify.

        Returns:
            TrendAnalysis containing identified trends.
        """
        if not items:
            logger.warning(f"[{period}] No items to analyze - returning empty analysis")
            return TrendAnalysis(
                date=utcnow(),
                period=period,
                trends=[],
                raw_article_count=0,
                sources_analyzed=[],
            )

        analysis_items = items[: self.MAX_ARTICLES_PER_ANALYSIS]
        sources = list({item.source for item in analysis_items})
        categories = list({item.category for item in analysis_items})

        logger.info(
            f"[{period}] Analyzing {len(analysis_items)} items from {len(sources)} sources: {sources}"
        )

        if self.dry_run:
            logger.info(f"[{period}] [DRY RUN] Skipping LLM call")
            return self._create_mock_analysis(analysis_items, period, sources, categories)

        prompt = self._build_analysis_prompt(analysis_items, period, max_trends)
        logger.info(f"[{period}] Sending prompt to local LLM ({len(prompt)} chars)")

        try:
            llm_response = await self.router.route(
                prompt=prompt,
                system=self.SYSTEM_MESSAGE,
                task_type="trend_analysis",
                force_local=True,
                quality="normal",
                # 10 trends of full JSON run ~1,400-2,000 tokens; 4,096 leaves
                # headroom without approaching the provider's num_ctx window.
                # Left unset, Ollama imposes no explicit output budget and the
                # only stop is the context window itself — which is exactly
                # how the 2026-08 truncation presented.
                max_tokens=4096,
                response_schema=self.TRENDS_RESPONSE_SCHEMA,
            )
            response = llm_response.content

            response_len = len(response) if response else 0
            logger.info(
                f"[{period}] LLM response received: {response_len} chars (model: {llm_response.model})"
            )

            if not response or not response.strip():
                logger.error(f"[{period}] Empty response from LLM! repr={repr(response)}")
                return TrendAnalysis(
                    date=utcnow(),
                    period=period,
                    trends=[],
                    raw_article_count=len(analysis_items),
                    sources_analyzed=sources,
                    categories_analyzed=categories,
                )

            if response_len < 100:
                logger.warning(f"[{period}] Suspiciously short response: {response}")

            trends = self._parse_trends_response(response, period)
            logger.info(f"[{period}] Parsed {len(trends)} trends successfully")

            if len(trends) == 0:
                logger.warning(f"[{period}] No trends parsed! Response preview: {response[:500]}")

            return TrendAnalysis(
                date=utcnow(),
                period=period,
                trends=trends,
                raw_article_count=len(analysis_items),
                sources_analyzed=sources,
                categories_analyzed=categories,
            )

        except Exception as e:
            logger.error(f"[{period}] Trend analysis exception: {type(e).__name__}: {e}")
            import traceback

            logger.error(f"[{period}] Traceback: {traceback.format_exc()}")
            return TrendAnalysis(
                date=utcnow(),
                period=period,
                trends=[],
                raw_article_count=len(analysis_items),
                sources_analyzed=sources,
                categories_analyzed=categories,
            )

    def _build_analysis_prompt(
        self,
        items: list[FeedItem],
        period: str,
        max_trends: int,
    ) -> str:
        """
        Build the analysis prompt with grouped headlines.

        Args:
            items: Feed items to include.
            period: Time period label.
            max_trends: Maximum trends to request.

        Returns:
            Formatted prompt string.
        """
        # Group items by category
        grouped: dict[str, list[FeedItem]] = {}
        for item in items:
            if item.category not in grouped:
                grouped[item.category] = []
            grouped[item.category].append(item)

        # Build headlines section
        headlines_parts = []
        for category, category_items in grouped.items():
            headlines_parts.append(f"\n### {category.upper()}")
            for item in category_items[:15]:  # Limit per category
                summary_preview = (
                    item.summary[:80] + "..." if len(item.summary) > 80 else item.summary
                )
                headlines_parts.append(f"- [{item.source}] {item.title}\n  {summary_preview}")

        headlines_text = "\n".join(headlines_parts)

        # Map period to human-readable
        period_labels = {
            "24h": "last 24 hours",
            "1w": "past week",
            "1m": "past month",
        }
        period_label = period_labels.get(period, period)

        return f"""Analyze these {period_label} news headlines to identify the top {max_trends} trending topics.

## Headlines by Category
{headlines_text}

## Instructions
Identify the most significant trends from these headlines. For each trend:

### Title Requirements (IMPORTANT)
- **Write specific and descriptive titles (minimum 30 characters)**
- Include specific technology names, project names, and numbers instead of generic expressions
- Bad examples: "AI Trend", "DeFi Growth", "NFT News"
- Good examples: "OpenAI GPT-5 Agent SDK Launch Accelerates Autonomous AI Workflow Automation", "Uniswap v4 Hooks Enable Custom DEX Strategies"

### Content Requirements
- summary should be at least 200 characters, explaining the background, current status, and impact of the trend in detail
- web3_relevance should include specific application scenarios and expected effects
- idea_seeds should each describe implementable project ideas in detail

**IMPORTANT: All content MUST be written in English only.**

Respond with a JSON object in this exact format:
```json
{{
  "trends": [
    {{
      "topic": "OpenAI GPT-5 Agent SDK Launch Marks the Beginning of Autonomous AI Workflow Automation Era",
      "keywords": ["GPT-5", "AI Agent", "autonomous workflow", "LLM orchestration", "tool use"],
      "summary": "OpenAI has officially released the Agent SDK alongside GPT-5, marking the full-scale adoption of AI agent development. This SDK natively supports tool use, memory management, and multi-step reasoning. Enterprises have begun automating complex business processes using these capabilities. Agent adoption is accelerating particularly in finance, healthcare, and legal sectors, while the developer community is producing various open-source frameworks.",
      "category": "ai",
      "score": 9.2,
      "article_count": 15,
      "sources": ["TechCrunch", "Hacker News", "OpenAI Blog"],
      "sample_headlines": ["OpenAI Releases Agent SDK with Native Tool Use", "GPT-5 Powers New Wave of Autonomous Business Agents"],
      "web3_relevance": "AI agents can be used for automatic rebalancing of DeFi protocols, DAO proposal analysis and voting automation, and smart contract security audit automation. Combined with on-chain data analysis, real-time market response strategies become possible.",
      "idea_seeds": [
        "DeFi Portfolio Auto-Rebalancing Agent - Automatically adjusts positions based on user risk preferences",
        "DAO Governance Participation Agent - Analyzes proposals and votes on behalf of token holders",
        "Smart Contract Security Audit Automation Tool - AI detects vulnerabilities and generates reports"
      ]
    }}
  ]
}}
```

Focus on actionable insights and Web3 opportunities. Be specific and detailed. Write everything in English."""

    def _parse_trends_response(
        self,
        response: str,
        period: str,
    ) -> list[Trend]:
        """
        Parse Claude's response into Trend objects.

        Args:
            response: Raw response from Claude.
            period: Time period for the analysis.

        Returns:
            List of Trend objects.
        """
        trends = []

        # Debug: Log raw response length and preview
        logger.debug(f"Raw response length: {len(response)} chars")
        if len(response) < 500:
            logger.debug(f"Full response: {response}")
        else:
            logger.debug(f"Response preview (first 500 chars): {response[:500]}...")

        # Layered extraction. gemma3:4b wraps JSON in prose ("Okay, here's
        # the JSON…"), regularly uses curly “smart quotes” as string
        # delimiters, and — before num_ctx was fixed — got truncated before
        # the closing fence. Each layer handles one of those defects; the
        # first one that yields a dict wins.
        data = None
        for tag, candidate in self._json_candidates(response):
            data = self._loads_lenient(candidate)
            if data is not None:
                logger.info(f"Parsed trends JSON via '{tag}' extraction")
                break

        if data is None:
            # Truncated tail: pull whatever complete objects exist inside the
            # "trends" array. A cut-off after trend 7 of 10 still yields 7.
            salvaged = self._salvage_trend_objects(response)
            if salvaged:
                logger.warning(
                    f"Trends JSON malformed or truncated; salvaged "
                    f"{len(salvaged)} complete trend objects from the array"
                )
                data = {"trends": salvaged}

        if data is None:
            preview = response[:150].replace("\n", " ")
            logger.error(f"Could not parse any JSON from response; preview: {preview!r}")
            logger.info("Attempting fallback text parsing...")
            trends = self._parse_trends_fallback(response, period)
            return sorted(trends, key=lambda t: t.score, reverse=True)

        if "trends" not in data:
            logger.warning("Response missing 'trends' key")
            return trends

        for trend_data in data["trends"]:
            try:
                trend = Trend(
                    topic=trend_data.get("topic", "Unknown"),
                    keywords=trend_data.get("keywords", []),
                    score=float(trend_data.get("score", 5.0)),
                    time_period=period,
                    sources=trend_data.get("sources", []),
                    article_count=int(trend_data.get("article_count", 0)),
                    sample_headlines=trend_data.get("sample_headlines", []),
                    category=trend_data.get("category", "general"),
                    summary=trend_data.get("summary", ""),
                    web3_relevance=trend_data.get("web3_relevance", ""),
                    idea_seeds=trend_data.get("idea_seeds", []),
                )
                trends.append(trend)
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to parse trend: {e}")
                continue

        return sorted(trends, key=lambda t: t.score, reverse=True)

    # -- lenient JSON extraction ------------------------------------------
    #
    # These exist because the production model (gemma3:4b) does not reliably
    # emit machine-clean JSON. Observed on 2026-08-05, from live responses:
    # prose before the fence, curly quotes as string delimiters (json.loads
    # dies mid-document), and truncation that eats the closing fence.

    # Double-quote lookalikes the model substitutes for '"'. Single curly
    # quotes are left alone: inside a string they are legal content, and as
    # delimiters they would not be valid JSON either way.
    _SMART_QUOTES = ("“", "”", "„", "‟")

    @classmethod
    def _normalize_json_quotes(cls, text: str) -> str:
        for q in cls._SMART_QUOTES:
            text = text.replace(q, '"')
        return text

    @staticmethod
    def _strip_trailing_commas(text: str) -> str:
        """Remove ",}" / ",]" — the other habitual small-model JSON error."""
        return re.sub(r",(\s*[}\]])", r"\1", text)

    @classmethod
    def _loads_lenient(cls, text: str) -> Optional[dict]:
        """json.loads with progressively more repair; None if nothing parses.

        Repairs are only attempted after a strict parse fails, so well-formed
        content is never altered.
        """
        candidates = (
            text,
            cls._normalize_json_quotes(text),
            cls._strip_trailing_commas(cls._normalize_json_quotes(text)),
        )
        for candidate in candidates:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
        return None

    @classmethod
    def _json_candidates(cls, response: str):
        """Yield (tag, substring) candidates, most precise first."""
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
        if fenced:
            yield "fenced", fenced.group(1)
        # No "after-```json-to-end" candidate: for a fence whose closing ```
        # was truncated away, _salvage_trend_objects recovers everything such
        # a layer would (verified by mutation — adding it changes no test).
        balanced = cls._extract_balanced_object(response)
        if balanced:
            yield "balanced-braces", balanced
        yield "raw", response

    @staticmethod
    def _extract_balanced_object(text: str) -> Optional[str]:
        """Slice from the first '{' to its matching '}', tracking strings."""
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None  # never balanced (truncated) — salvage handles that case

    @classmethod
    def _salvage_trend_objects(cls, response: str) -> list[dict]:
        """Recover complete objects from a truncated "trends" array.

        Normalizes quotes first (the salvage path is only reached after strict
        parsing failed), finds the array opening, then raw_decode()s one
        object at a time until the truncated tail stops parsing.
        """
        text = cls._strip_trailing_commas(cls._normalize_json_quotes(response))
        array_start = re.search(r'"trends"\s*:\s*\[', text)
        if not array_start:
            return []
        decoder = json.JSONDecoder()
        objects: list[dict] = []
        pos = array_start.end()
        while pos < len(text):
            while pos < len(text) and text[pos] in " \t\r\n,":
                pos += 1
            if pos >= len(text) or text[pos] != "{":
                break
            try:
                obj, pos = decoder.raw_decode(text, pos)
            except json.JSONDecodeError:
                break  # truncated mid-object: keep what we have
            if isinstance(obj, dict):
                objects.append(obj)
        return objects

    def _parse_trends_fallback(
        self,
        response: str,
        period: str,
    ) -> list[Trend]:
        """
        Fallback parsing when JSON parsing fails.

        Attempts to extract trends from structured text.
        """
        trends = []

        # Look for numbered trends
        trend_pattern = r"(?:^|\n)\d+\.\s*\*?\*?([^*\n]+)\*?\*?"
        matches = re.findall(trend_pattern, response)

        for i, topic in enumerate(matches[:10]):
            topic = topic.strip()
            if topic:
                trends.append(
                    Trend(
                        topic=topic,
                        keywords=[],
                        score=10.0 - i,  # Decreasing score by position
                        time_period=period,
                        sources=[],
                        article_count=0,
                        sample_headlines=[],
                        category="general",
                        summary="(Parsed from text fallback)",
                        web3_relevance="",
                        idea_seeds=[],
                    )
                )

        return trends

    def _create_mock_analysis(
        self,
        items: list[FeedItem],
        period: str,
        sources: list[str],
        categories: list[str],
    ) -> TrendAnalysis:
        """Create mock analysis for dry run mode."""
        mock_trends = [
            Trend(
                topic="Mock AI Trend",
                keywords=["ai", "llm", "agents"],
                score=9.0,
                time_period=period,
                sources=sources[:3],
                article_count=len(items),
                sample_headlines=["Mock headline 1", "Mock headline 2"],
                category="ai",
                summary="This is a mock trend for testing purposes.",
                web3_relevance="Could be integrated with blockchain for transparency.",
                idea_seeds=["Mock idea 1", "Mock idea 2"],
            ),
            Trend(
                topic="Mock Crypto Trend",
                keywords=["defi", "protocol", "token"],
                score=8.5,
                time_period=period,
                sources=sources[:2],
                article_count=len(items) // 2,
                sample_headlines=["Mock crypto headline"],
                category="crypto",
                summary="Another mock trend for testing.",
                web3_relevance="Directly related to Web3.",
                idea_seeds=["Mock DeFi idea"],
            ),
        ]

        return TrendAnalysis(
            date=utcnow(),
            period=period,
            trends=mock_trends,
            raw_article_count=len(items),
            sources_analyzed=sources,
            categories_analyzed=categories,
        )

    async def analyze_all_periods(
        self,
        items: list[FeedItem],
    ) -> dict[str, TrendAnalysis]:
        """
        Analyze trends across all configured time periods.

        Args:
            items: All fetched feed items.

        Returns:
            Dictionary mapping period to TrendAnalysis.
        """
        from .feeds import FeedFetcher

        fetcher = FeedFetcher(self.config)
        results: dict[str, TrendAnalysis] = {}

        periods = self.config.get("trends", "periods", default=["24h", "1w", "1m"])

        for period in periods:
            filtered_items = fetcher.filter_by_period(items, period)
            analysis = await self.analyze_trends(filtered_items, period)
            results[period] = analysis
            logger.info(
                f"Analyzed {period}: {len(analysis.trends)} trends from "
                f"{analysis.raw_article_count} articles"
            )

        return results
