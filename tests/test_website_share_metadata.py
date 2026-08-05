"""Regression guards for the unified cross-site title/share convention.

PR #2922 unified the browser-title / Open Graph / Twitter convention at the
root layout, but the four ``/{ideas,plans,projects,signals}/[id]`` detail
routes kept their own pre-convention metadata (``Plan - MOSS.AO``, siteName
``MOSS.AO``, twitter card ``summary``). Next.js merges metadata shallowly — a
child ``openGraph`` replaces the root object wholesale — so any route that
restates share metadata inline also silently drops the shared og:image and
siteName. The fix centralizes everything in ``website/src/lib/metadata.ts``.

The website has no JS test runner, so these pins are source-level, in the same
spirit as test_deploy.py pinning "``git clean`` appears nowhere in deploy.sh":
they fail on the commit that reintroduces inline share metadata, not on the
next visual QA pass.
"""

from pathlib import Path

import pytest

WEBSITE_SRC = Path(__file__).resolve().parents[1] / "website" / "src"

DETAIL_PAGES = {
    "Idea": WEBSITE_SRC / "app" / "ideas" / "[id]" / "page.tsx",
    "Plan": WEBSITE_SRC / "app" / "plans" / "[id]" / "page.tsx",
    "Project": WEBSITE_SRC / "app" / "projects" / "[id]" / "page.tsx",
    "Signal": WEBSITE_SRC / "app" / "signals" / "[id]" / "page.tsx",
}


def _read(path: Path) -> str:
    assert path.is_file(), f"expected source file missing: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("kind", sorted(DETAIL_PAGES), ids=str.lower)
class TestDetailRouteMetadata:
    def test_uses_shared_helper(self, kind):
        source = _read(DETAIL_PAGES[kind])
        assert (
            "from '@/lib/metadata'" in source
        ), f"{kind} detail route must build its metadata via the shared helper"
        assert f"detailMetadata('{kind}'" in source

    def test_does_not_restate_share_metadata_inline(self, kind):
        # Inline openGraph/twitter objects are how the og:image and siteName
        # got dropped in the first place (shallow merge). Everything belongs
        # in website/src/lib/metadata.ts.
        source = _read(DETAIL_PAGES[kind])
        for marker in ("openGraph", "twitter", "siteName"):
            assert marker not in source, f"{kind} detail route restates '{marker}' inline"

    def test_old_brand_strings_gone(self, kind):
        source = _read(DETAIL_PAGES[kind])
        assert "- MOSS.AO" not in source, f"{kind} detail route still uses the pre-#2922 title"


class TestSharedConvention:
    def test_helper_pins_family_convention(self):
        source = _read(WEBSITE_SRC / "lib" / "metadata.ts")
        assert "SITE_NAME = 'Mossland'" in source
        assert "'%s — MOSS.AO · Mossland'" in source
        # Pin the *usage* inside detailMetadata(), not just the OG_IMAGE
        # constant — the constant stays alive via layout.tsx, so a bare
        # "og-image.png" check stays green even if detail routes lose images.
        assert "images: [OG_IMAGE]" in source, "detailMetadata must attach the shared og:image"
        assert "og-image.png" in source
        assert "summary_large_image" in source

    def test_root_layout_uses_title_template(self):
        # A plain-string root title cannot brand child titles; the
        # default/template pair is what makes 'Plan' render as
        # 'Plan — MOSS.AO · Mossland'.
        source = _read(WEBSITE_SRC / "app" / "layout.tsx")
        assert 'from "@/lib/metadata"' in source
        assert "default: SITE_TITLE" in source
        assert "template: TITLE_TEMPLATE" in source


class TestEcosystemBarAccessibility:
    def test_new_tab_hint_translated_in_both_locales(self):
        source = _read(WEBSITE_SRC / "lib" / "i18n.tsx")
        assert (
            source.count("'ecosystem.newTab':") == 2
        ), "ecosystem.newTab must exist in exactly the en and ko translation tables"

    def test_footer_announces_new_tab(self):
        source = _read(WEBSITE_SRC / "components" / "Footer.tsx")
        assert "ecosystem.newTab" in source
        assert "sr-only" in source

    def test_footer_separates_site_name_from_description(self):
        # The explicit {' '} text node is what keeps the accessible name from
        # collapsing to "BRIDGEGovernance OS" — CSS margins add no text.
        source = _read(WEBSITE_SRC / "components" / "Footer.tsx")
        assert (
            source.count("{site.name}{' '}") == 2
        ), "both the current-site and link branches need a real space after the site name"
