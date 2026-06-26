"""Tests for ContentTranslator (translation/translator.py).

Previously had zero coverage. The LLM call is replaced by a FakeRouter so the
language detection, already-in-target-language short-circuits, model-wrapper
stripping, and bilingual orchestration are exercised deterministically.
"""

import pytest

from agentic_orchestrator.translation.translator import ContentTranslator


class FakeResponse:
    def __init__(self, content, model="fake-model"):
        self.content = content
        self.model = model


class FakeRouter:
    """Records calls and returns a canned translation."""

    def __init__(self, reply="TRANSLATED"):
        self.reply = reply
        self.calls = []

    async def route(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.reply)


@pytest.fixture
def translator():
    return ContentTranslator(router=FakeRouter())


class TestDetectLanguage:
    def test_korean(self, translator):
        assert translator._detect_language("안녕하세요 반갑습니다 여러분") == "ko"

    def test_english(self, translator):
        assert translator._detect_language("Hello world this is English text") == "en"

    def test_empty_defaults_to_english(self, translator):
        assert translator._detect_language("") == "en"

    def test_numbers_and_symbols_only(self, translator):
        assert translator._detect_language("12345 !@#$% 67890") == "en"

    def test_mostly_english_with_a_little_korean(self, translator):
        # 3 Korean chars vs many ASCII letters -> ratio <= 0.3 -> "en"
        assert translator._detect_language("Mossland NFT portfolio 트래커") == "en"

    def test_mostly_korean(self, translator):
        assert translator._detect_language("모스랜드 NFT 가치 평가 대시보드 서비스") == "ko"


class TestTranslateShortCircuits:
    async def test_to_english_skips_when_already_english(self, translator):
        out = await translator.translate_to_english("This text is already in English")
        assert out == "This text is already in English"
        assert translator.router.calls == []  # LLM not invoked

    async def test_to_korean_skips_when_already_korean(self, translator):
        text = "이미 한국어로 작성된 텍스트입니다"
        out = await translator.translate_to_korean(text)
        assert out == text
        assert translator.router.calls == []

    async def test_to_english_empty_returns_empty(self, translator):
        assert await translator.translate_to_english("   ") == ""

    async def test_to_korean_empty_returns_empty(self, translator):
        assert await translator.translate_to_korean("") == ""


class TestWrapperStripping:
    async def test_strips_prefix_and_trailing_separator_ko_to_en(self):
        router = FakeRouter(reply="English translation: Hello world\n---")
        t = ContentTranslator(router=router)
        out = await t.translate_to_english("한국어 텍스트를 영어로 번역해 주세요 부탁합니다")
        assert out == "Hello world"
        assert len(router.calls) == 1

    async def test_strips_prefix_en_to_ko(self):
        router = FakeRouter(reply="Korean translation: 안녕하세요")
        t = ContentTranslator(router=router)
        out = await t.translate_to_korean("Please translate this English sentence to Korean")
        assert out == "안녕하세요"

    async def test_translation_failure_returns_empty(self):
        class BoomRouter:
            async def route(self, **kwargs):
                raise RuntimeError("llm down")

        t = ContentTranslator(router=BoomRouter())
        out = await t.translate_to_english("한국어 텍스트 번역 요청 실패 케이스 테스트")
        assert out == ""


class TestEnsureBilingual:
    async def test_korean_input_keeps_korean_translates_english(self):
        router = FakeRouter(reply="English version")
        t = ContentTranslator(router=router)
        korean = "한국어 원본 텍스트입니다 영어로 번역되어야 합니다"
        en, ko = await t.ensure_bilingual(korean)
        assert ko == korean
        assert en == "English version"

    async def test_english_input_keeps_english_translates_korean(self):
        router = FakeRouter(reply="한국어 번역본")
        t = ContentTranslator(router=router)
        english = "English original content that should be translated to Korean"
        en, ko = await t.ensure_bilingual(english)
        assert en == english
        assert ko == "한국어 번역본"

    async def test_empty_returns_pair_of_empties(self, translator):
        assert await translator.ensure_bilingual("") == ("", "")
