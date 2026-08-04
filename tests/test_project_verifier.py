"""Tests for CodeVerifier (project/verifier.py).

These are deterministic regardless of whether ``solc``/``esbuild`` are installed
on the host: tool-dependent checks are exercised with the tool explicitly
disabled, so the suite asserts the graceful-degradation contract rather than the
presence of a compiler.
"""

from agentic_orchestrator.project.verifier import (
    JAVASCRIPT,
    PYTHON,
    SOLIDITY,
    TYPESCRIPT,
    UNKNOWN,
    CodeVerifier,
    VerificationStatus,
    _esbuild_loader,
    detect_language,
)


class TestDetectLanguage:
    def test_known_extensions(self):
        assert detect_language("a/b/Main.sol") == SOLIDITY
        assert detect_language("app/main.py") == PYTHON
        assert detect_language("x.ts") == TYPESCRIPT
        assert detect_language("x.tsx") == TYPESCRIPT
        assert detect_language("x.js") == JAVASCRIPT
        assert detect_language("x.jsx") == JAVASCRIPT

    def test_module_typescript_extensions(self):
        assert detect_language("x.mts") == TYPESCRIPT
        assert detect_language("x.cts") == TYPESCRIPT
        assert detect_language("x.mjs") == JAVASCRIPT
        assert detect_language("x.cjs") == JAVASCRIPT

    def test_unknown_extensions(self):
        assert detect_language("README.md") == UNKNOWN
        assert detect_language(".moss-project.json") == UNKNOWN
        assert detect_language("Dockerfile") == UNKNOWN


class TestEsbuildLoader:
    """Plain .ts must use the `ts` loader, not `tsx` (review must-fix)."""

    def test_loader_per_extension(self):
        assert _esbuild_loader("a.ts") == "ts"
        assert _esbuild_loader("a.tsx") == "tsx"
        assert _esbuild_loader("a.mts") == "ts"
        assert _esbuild_loader("a.cts") == "ts"
        assert _esbuild_loader("a.jsx") == "jsx"
        assert _esbuild_loader("a.js") == "js"
        assert _esbuild_loader("a.mjs") == "js"


class TestPythonVerification:
    def setup_method(self):
        self.v = CodeVerifier()

    def test_valid_python_passes(self):
        r = self.v.verify("app/main.py", "def f():\n    return 1\n")
        assert r.status == VerificationStatus.PASSED
        assert r.checker == "py-compile"
        assert r.ok

    def test_syntax_error_fails_with_line(self):
        r = self.v.verify("app/bad.py", "def f(:\n    pass\n")
        assert r.status == VerificationStatus.FAILED
        assert not r.ok
        assert any("SyntaxError" in e for e in r.errors)

    def test_pep701_fstring_compiles(self):
        # The generator emits f-strings reusing the outer quote (PEP 701).
        src = 'x = 1\nprint(f"value: {x}")\n'
        assert self.v.verify("a.py", src).status == VerificationStatus.PASSED


class TestEmptyFiles:
    def test_empty_content_fails(self):
        v = CodeVerifier()
        for path in ("a.py", "C.sol", "x.ts"):
            r = v.verify(path, "   \n  ")
            assert r.status == VerificationStatus.FAILED
            assert "empty" in r.errors[0]


class TestSolidityStatic:
    def setup_method(self):
        # solc disabled: every Solidity result is static-only and deterministic.
        self.v = CodeVerifier(enable_solc=False)

    def test_length_call_is_flagged(self):
        src = (
            "// SPDX-License-Identifier: MIT\n"
            "pragma solidity ^0.8.20;\n"
            "contract C {\n"
            "  function f(string memory s) public pure returns (uint) { return s.length(); }\n"
            "}\n"
        )
        r = self.v.verify("C.sol", src)
        assert r.status == VerificationStatus.FAILED
        assert any(".length()" in e for e in r.errors)

    def test_missing_pragma_is_flagged(self):
        r = self.v.verify("C.sol", "contract C { uint x; }")
        assert r.status == VerificationStatus.FAILED
        assert any("pragma" in e for e in r.errors)

    def test_unbalanced_braces_flagged_as_truncation(self):
        src = "pragma solidity ^0.8.20;\ncontract D {\n  function f() public {\n"
        r = self.v.verify("D.sol", src)
        assert r.status == VerificationStatus.FAILED
        assert any("unbalanced" in e for e in r.errors)

    def test_braces_inside_strings_do_not_false_positive(self):
        src = (
            "pragma solidity ^0.8.20;\n"
            'contract G {\n  string s = "a { b } c";\n  function f() public {}\n}\n'
        )
        r = self.v.verify("G.sol", src)
        # No static errors -> skipped (solc disabled), not failed.
        assert r.status == VerificationStatus.SKIPPED

    def test_clean_contract_with_imports_is_skipped(self):
        src = (
            "// SPDX-License-Identifier: MIT\n"
            "pragma solidity ^0.8.20;\n"
            'import "@openzeppelin/contracts/access/Ownable.sol";\n'
            "contract C is Ownable {}\n"
        )
        r = self.v.verify("C.sol", src)
        assert r.status == VerificationStatus.SKIPPED
        assert r.ok  # skipped is not a failure


class TestToolDegradation:
    def test_typescript_skipped_when_esbuild_disabled(self):
        v = CodeVerifier(enable_esbuild=False)
        r = v.verify("x.ts", "const a: number = 1;\nexport default a;\n")
        assert r.status == VerificationStatus.SKIPPED
        assert r.ok

    def test_unknown_language_skipped(self):
        v = CodeVerifier()
        r = v.verify("README.md", "# hello")
        assert r.status == VerificationStatus.SKIPPED

    def test_result_to_dict_is_serializable(self):
        v = CodeVerifier()
        d = v.verify("a.py", "x = 1\n").to_dict()
        assert set(d) == {"path", "language", "status", "checker", "errors", "repaired"}
