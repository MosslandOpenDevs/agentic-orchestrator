"""Titles must reach the reader as plain text.

19.0% of ideas carried leaked markdown in at least one language, and 431 public
GitHub issues read ``[Idea] Idea: ...``. Three independent writers produced it —
a prompt rule left over from a pre-JSON era, the translator, and a bare f-string
in backlog triage — so the cleaning lives in one place and every writer calls it.
"""

from agentic_orchestrator.textutil import clean_issue_title, clean_title


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
        assert clean_title("## 아이디어: 브라우저 지갑 가스비 상한 설정") == "브라우저 지갑 가스비 상한 설정"

    def test_unwraps_emphasis_around_the_whole_title(self):
        assert clean_title("**제네시스: 분산형 위협 인텔리전스**") == "제네시스: 분산형 위협 인텔리전스"

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
        assert clean_issue_title("Deploy **wstETH** vaults on Base") == "Deploy wstETH vaults on Base"

    def test_removes_the_duplicated_idea_label(self):
        """``[Idea] Idea: ...`` appeared on 431 public issues: the issue builder
        stripped ``#`` but left the word."""
        assert clean_issue_title("## Idea: Gas-Guard Copilot") == "Gas-Guard Copilot"

    def test_keeps_underscores_that_belong_to_identifiers(self):
        assert "title_ko" in clean_issue_title("Fix title_ko rendering in the ideas list")
