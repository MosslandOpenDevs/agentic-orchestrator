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


# Where a serialized object or list starts leaking into a field that should hold
# a phrase. Two production names, verbatim:
#
#   ...Growing Demand for Supply Chain Tracking in Web3”, “keywords”: [“Provenance”, …
#   ...Sparks Innovation in Synthetic Media”, 2608.06411v1, “MLLM Attention Pruning”, …
#
# Note the typographic quotes -- a straight-quote-only pattern matches neither --
# and that the second leak is a bare list, not a keyed object, so a rule written
# around `"keywords":` would miss it. What both share is a closing quote, a
# comma, and then the start of ANOTHER serialized value.
#
# That lookahead is the whole guard. Without it the rule cut ordinary prose:
# `"Proof of Play", a Verifiable Session Attestation Layer` became
# `"Proof of Play`, and `The rise of “AI agents”, DePIN, and RWA` became
# `The rise of “AI agents`. Both go straight to `trends.name` on every analysis
# cycle, with no copy of the original kept anywhere.
_SERIALIZED_TAIL = re.compile(r"""["'“”‘’]\s*,\s*(?=["'“”‘’]|\d)""")

# A cut that leaves less than this is far likelier to be a false positive than
# a real rescue: the project's own floor for a title is 30 characters.
_MIN_NAME_AFTER_CUT = 30


def clean_name(value: object, limit: int = 200) -> str:
    """``clean_title`` plus the two ways a *generated* name fails.

    Applied to trend names rather than to titles generally: trend names come
    straight from the analyzer's own prose field, while idea and plan titles are
    read out of a parsed JSON value and cannot pick up a sibling key this way.
    """
    text = clean_title(value)

    tail = _SERIALIZED_TAIL.search(text)
    if tail and tail.start() >= _MIN_NAME_AFTER_CUT:
        text = text[: tail.start()].rstrip()

    if len(text) > limit:
        # Cut on a word boundary; a name sliced mid-word reads as corruption.
        cut = text[:limit]
        space = cut.rfind(" ")
        text = (cut[:space] if space > limit // 2 else cut).rstrip()

    return text.rstrip(" ,;:-–—")


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
    # Removing the emphasis can expose a label that was hidden inside it --
    # `[Idea] **Idea:** X` only becomes `[Idea] Idea: X` on the first pass -- so
    # run the leading-marker rules again over the result. Without this the
    # command whose entire purpose is fixing 431 `[Idea] Idea:` titles left them
    # one pass short, and a second run would rename the same public issue again.
    return clean_title(re.sub(r"\s+", " ", text).strip())
