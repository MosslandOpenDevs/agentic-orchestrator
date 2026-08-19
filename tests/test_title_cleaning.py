"""Titles must reach the reader as plain text.

19.0% of ideas carried leaked markdown in at least one language, and 431 public
GitHub issues read ``[Idea] Idea: ...``. Three independent writers produced it —
a prompt rule left over from a pre-JSON era, the translator, and a bare f-string
in backlog triage — so the cleaning lives in one place and every writer calls it.
"""

from agentic_orchestrator.textutil import clean_issue_title, clean_name, clean_title


class TestCleanTitle:
    def test_strips_the_heading_and_the_idea_label(self):
        """The exact shape that reached production: the model obeyed a prompt
        rule telling it to start with `## Idea:` and put the heading inside the
        JSON string value."""
        assert (
            clean_title("## Idea: ERC-6551 Token-Bound Spend Passport for Quest Players")
            == "ERC-6551 Token-Bound Spend Passport for Quest Players"
        )

    def test_strips_the_korean_label(self):
        assert (
            clean_title("## 아이디어: 브라우저 지갑 가스비 상한 설정")
            == "브라우저 지갑 가스비 상한 설정"
        )

    def test_unwraps_emphasis_around_the_whole_title(self):
        assert (
            clean_title("**제네시스: 분산형 위협 인텔리전스**")
            == "제네시스: 분산형 위협 인텔리전스"
        )

    def test_handles_stacked_markers(self):
        assert clean_title("> ### **Idea: Session-Key Budget Vault**") == "Session-Key Budget Vault"

    def test_keeps_the_plan_prefix_the_pipeline_adds_on_purpose(self):
        """``Plan:`` and ``계획:`` distinguish a plan from the idea it came
        from. Only labels that carry no information are noise."""
        assert clean_title("Plan: Mossland Quest Rewards") == "Plan: Mossland Quest Rewards"
        assert clean_title("## 계획: 지갑 가스비 상한") == "계획: 지갑 가스비 상한"

    def test_the_f_string_and_heading_combination(self):
        """``backlog_triage`` builds ``f"Plan: {idea.title_ko}"``. When the idea
        title was itself dirty the result was ``Plan: ## Mossland ...`` — which
        the frontend's anchored regex could not match either, so it reached the
        page with the hashes visible."""
        assert clean_title("Plan: ## Mossland Wallet Guard") == "Plan: ## Mossland Wallet Guard"
        # ...which is why the cleaner runs on the idea title *before* the
        # f-string wraps it, not on the result.
        assert clean_title("## Mossland Wallet Guard") == "Mossland Wallet Guard"

    def test_leaves_a_clean_title_untouched(self):
        title = "EIP-7702 Intent Vault and Paymaster Yield Router for Wallet Power Users"

        assert clean_title(title) == title

    def test_does_not_eat_emphasis_inside_a_title(self):
        """Removing markers from the middle changes the wording rather than
        removing decoration; the h3 renderer is fine with it."""
        assert clean_title("Deploy **wstETH** vaults on Base") == "Deploy **wstETH** vaults on Base"

    def test_collapses_whitespace_and_handles_empty_input(self):
        assert clean_title("##  Idea:   Spaced   Out  Title") == "Spaced Out Title"
        assert clean_title(None) == ""
        assert clean_title("") == ""
        assert clean_title("   ") == ""

    def test_terminates_on_adversarial_input(self):
        assert clean_title("#" * 500 + " x").endswith("x")
        assert clean_title("*" * 200) != ""


class TestCleanIssueTitle:
    def test_removes_emphasis_github_will_not_render(self):
        assert (
            clean_issue_title("Deploy **wstETH** vaults on Base") == "Deploy wstETH vaults on Base"
        )

    def test_removes_the_duplicated_idea_label(self):
        """``[Idea] Idea: ...`` appeared on 431 public issues: the issue builder
        stripped ``#`` but left the word."""
        assert clean_issue_title("## Idea: Gas-Guard Copilot") == "Gas-Guard Copilot"

    def test_keeps_underscores_that_belong_to_identifiers(self):
        assert "title_ko" in clean_issue_title("Fix title_ko rendering in the ideas list")


class TestCleanName:
    """Trend names come from the analyzer's own prose field, and the serialized
    object it was parsed out of sometimes comes along."""

    # Verbatim from production (trend list, 2026-08-18). Note the typographic
    # quotes: a straight-quote pattern matches none of this.
    LEAKED = (
        "Provenance Blockchain’s Token Surge Signals Growing Demand for Enhanced "
        "Supply Chain Tracking in Web3”,  “keywords”: "
        "[“Provenance”, “HASH token”, “supply chain”], "
        "“score”: 8.7"
    )
    LEAKED_LIST = (
        "OpenAI’s Sora AI Image Generation Tool Sparks Innovation in Content "
        "Creation & Synthetic Media”, 2608.06411v1, “MLLM Attention Pruning”, "
        "95.5 ARC-AGI-3 Score"
    )

    def test_cuts_the_serialized_object_off_a_name(self):
        cleaned = clean_name(self.LEAKED)

        assert cleaned.endswith("in Web3")
        assert "keywords" not in cleaned
        assert "8.7" not in cleaned

    def test_cuts_a_leaked_list_too(self):
        """Not every leak is a keyed object — this one is a bare list tail, so
        a rule keyed on `"keywords":` would miss it. The reliable signal is a
        closing quote followed by a comma."""
        cleaned = clean_name(self.LEAKED_LIST)

        assert cleaned.endswith("Synthetic Media")
        assert "2608.06411v1" not in cleaned

    def test_bounds_the_length_on_a_word_boundary(self):
        name = " ".join(["Mossland"] * 80)  # ~720 chars

        cleaned = clean_name(name, limit=200)

        assert len(cleaned) <= 200
        assert not cleaned.endswith("Mossla"), "a name cut mid-word reads as corruption"

    def test_leaves_an_ordinary_name_alone(self):
        name = "Firelock-AI/kin & Trinity: Triune Architecture for AGI Long-Term Memory"

        assert clean_name(name) == name

    def test_still_strips_markdown_like_clean_title(self):
        assert clean_name("## 아이디어: 지갑 가스비 상한") == "지갑 가스비 상한"

    def test_empty_input(self):
        assert clean_name(None) == ""
        assert clean_name("") == ""


class TestCleanNameDoesNotCutOrdinaryProse:
    """The cut rule writes straight to ``trends.name`` on every analysis cycle,
    with no copy of the original kept — so a false positive is unrecoverable
    data loss, not a cosmetic slip. Both of these were truncated before the
    lookahead was added."""

    def test_a_quoted_phrase_followed_by_prose_survives(self):
        name = '"Proof of Play", a Verifiable Session Attestation Layer for Mossland Quests'

        assert clean_name(name) == name

    def test_a_quoted_term_in_a_list_of_words_survives(self):
        name = "The rise of “AI agents”, DePIN, and RWA tokenization in Q3 2026"

        assert clean_name(name) == name

    def test_an_apostrophe_before_a_comma_survives(self):
        name = "Mossland's Treasury, Rebalanced: An On-Chain Allocation Engine for MOC"

        assert clean_name(name) == name

    def test_the_real_leak_is_still_cut(self):
        leaked = (
            "Provenance Blockchain Token Surge Signals Demand for Supply Chain "
            "Tracking in Web3”, “keywords”: [“Provenance”], “score”: 8.7"
        )

        cleaned = clean_name(leaked)

        assert cleaned.endswith("in Web3")
        assert "keywords" not in cleaned

    def test_a_cut_that_would_leave_a_stub_is_refused(self):
        """Below the project's own 30-character floor a cut is likelier to be a
        false positive than a rescue, so the name is left whole."""
        name = '"AI”, “x”: 1'

        assert clean_name(name) == name


class TestCleanIssueTitleIsAFixedPoint:
    """This one renames real issues on a public repository. Not being a fixed
    point means the command that exists to fix 431 ``[Idea] Idea:`` titles left
    them one pass short, and a second run renamed the same issue again."""

    def test_a_label_hidden_inside_emphasis_is_removed_in_one_pass(self):
        assert clean_issue_title("**Idea:** Gas-Guard Copilot") == "Gas-Guard Copilot"

    def test_running_it_twice_changes_nothing(self):
        for title in [
            "**Idea:** Gas-Guard Copilot",
            "## Idea: ERC-6551 Spend Passport",
            "Deploy **wstETH** vaults on Base",
            "Plan: Mossland Quest Rewards",
            "*__Idea:__* Session-Key Budget Vault",
        ]:
            once = clean_issue_title(title)
            assert clean_issue_title(once) == once, f"not a fixed point: {title!r} -> {once!r}"
