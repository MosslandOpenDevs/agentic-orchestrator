"""Title cleaning for every writer that puts a title into the database.

Titles are written by models and by the translator, and both of them emit
markdown. A title is not rendered as markdown anywhere it is used -- it goes
into an ``<h3>`` as a text node, into a GitHub issue title (which does not
render markdown at all), and into ``[Idea] ...`` issue prefixes -- so the markup
survives all the way to the reader as literal ``## Idea:``.

That is not hypothetical: 19.0% of ideas carried leaked markup in at least one
language, and 431 public issues read ``[Idea] Idea: ...``. There were three
independent sources (a stale prompt rule, the translator, and a bare f-string),
which is exactly why the cleaning belongs in one function that every writer
calls rather than in each writer.

The frontend has its own ``stripMarkdown`` for text that is already stored; this
is the write-side counterpart, so that new rows are clean at rest.
"""

import re

# One leading block marker: heading, blockquote, or a bullet.
_BLOCK_MARKER = re.compile(r"^\s*(?:>+\s*|#{1,6}\s+|[-*+]\s+)")

# A label the generator prepends and that carries no information, because the
# consumer already says what it is looking at ("[Idea] Idea: ..." in a GitHub
# title, an idea card on the ideas page). Deliberately excludes ``Plan:`` and
# ``계획:`` -- those are prefixes the pipeline adds on purpose to distinguish a
# plan from the idea it came from, and stripping them would erase real meaning.
_NOISE_LABEL = re.compile(r"^\s*(?:Idea|아이디어)\s*[:：]\s*", re.IGNORECASE)

# `**bold**`, `__bold__`, `*italic*`, `` `code` `` wrapping the entire title.
_WRAPPED = re.compile(r"^\s*(\*{1,3}|_{2}|`)(.+?)\1\s*$", re.DOTALL)

# Markers can stack -- `## Idea: **X**` needs three passes -- but the loop must
# terminate on adversarial input, so bound it.
_MAX_PASSES = 6


def _strip_once(text: str) -> str:
    """Remove at most one layer of decoration."""
    wrapped = _WRAPPED.match(text)
    if wrapped:
        return wrapped.group(2).strip()

    stripped = _BLOCK_MARKER.sub("", text, count=1)
    if stripped != text:
        return stripped.strip()

    return _NOISE_LABEL.sub("", text, count=1).strip()


def clean_title(value: object) -> str:
    """Return ``value`` as a plain-text title.

    Strips leading markdown block markers, an ``Idea:``/``아이디어:`` label, and
    emphasis wrapping the whole string; collapses whitespace. Emphasis *inside*
    a title is left alone -- removing it from the middle changes wording rather
    than removing decoration.

    >>> clean_title("## Idea: ERC-6551 Token-Bound Spend Passport")
    'ERC-6551 Token-Bound Spend Passport'
    >>> clean_title("Plan: Mossland Quest Rewards")
    'Plan: Mossland Quest Rewards'
    """
    if not value:
        return ""

    text = str(value).strip()
    for _ in range(_MAX_PASSES):
        nxt = _strip_once(text)
        if nxt == text:
            break
        text = nxt

    return re.sub(r"\s+", " ", text).strip()


def clean_issue_title(value: object) -> str:
    """Plain-text title for a GitHub issue.

    GitHub renders no markdown in issue titles, so anything left shows up as
    literal asterisks and hashes. On top of ``clean_title`` this also removes
    emphasis *inside* the string, where the alternative is a reader seeing
    ``[Idea] Deploy **wstETH** vaults``.
    """
    text = clean_title(value)
    text = re.sub(r"[*`]+", "", text)
    # `__bold__` only when it wraps a run. A bare underscore is left alone --
    # identifiers (`title_ko`, `idea_id`) legitimately contain one, and this
    # matches the frontend's `stripMarkdown` so both sides agree.
    text = re.sub(r"__([^_]+)__", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()
