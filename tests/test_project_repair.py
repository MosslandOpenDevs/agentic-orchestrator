"""Tests for the deterministic CodeRepairer (project/repair.py)."""

import json

from agentic_orchestrator.project.repair import (
    OZ_PACKAGE,
    OZ_VERSION,
    CodeRepairer,
    _normalize_oz_import_paths,
    _strip_ownable_base_call,
    ensure_contract_dependencies,
)
from agentic_orchestrator.project.verifier import CodeVerifier, VerificationStatus


class _File:
    """Minimal stand-in for TemplateFile/GeneratedFile (path + mutable content)."""

    def __init__(self, path, content):
        self.path = path
        self.content = content


class TestSolidityRepairs:
    def setup_method(self):
        self.r = CodeRepairer()

    def test_adds_spdx_and_pragma_when_missing(self):
        res = self.r.repair_file("C.sol", "contract C { uint x; }")
        assert "SPDX-License-Identifier" in res.content
        assert "pragma solidity" in res.content
        assert any("SPDX" in f for f in res.fixes)
        assert any("pragma" in f for f in res.fixes)

    def test_length_call_becomes_property(self):
        src = "pragma solidity ^0.8.20;\ncontract C { function f(bytes memory b) public pure returns (uint){ return b.length(); } }\n"
        res = self.r.repair_file("C.sol", src)
        assert "b.length" in res.content and "b.length()" not in res.content

    def test_now_becomes_block_timestamp(self):
        src = "pragma solidity ^0.8.20;\ncontract C { function f() public view returns (uint){ return now; } }\n"
        res = self.r.repair_file("C.sol", src)
        assert "block.timestamp" in res.content and "return now" not in res.content

    def test_oz_v5_import_paths_normalized_to_v4(self):
        src = (
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n"
            'import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";\n'
            'import "@openzeppelin/contracts/utils/Pausable.sol";\n'
            "contract C {}\n"
        )
        res = self.r.repair_file("C.sol", src)
        assert "security/ReentrancyGuard.sol" in res.content
        assert "security/Pausable.sol" in res.content
        assert "utils/ReentrancyGuard" not in res.content

    def test_ownable_v5_base_call_removed(self):
        src = (
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n"
            'import "@openzeppelin/contracts/access/Ownable.sol";\n'
            "contract C is Ownable { constructor() Ownable(msg.sender) {} }\n"
        )
        res = self.r.repair_file("C.sol", src)
        assert "Ownable(msg.sender)" not in res.content
        assert "is Ownable" in res.content  # inheritance left intact

    def test_strings_and_comments_are_preserved(self):
        src = (
            "pragma solidity ^0.8.20;\n"
            "contract C {\n"
            "  // mention now and x.length() in a comment\n"
            '  string s = "now and .length()";\n'
            "  function f() public {}\n"
            "}\n"
        )
        res = self.r.repair_file("C.sol", src)
        assert "now and x.length() in a comment" in res.content
        assert 'string s = "now and .length()";' in res.content

    def test_idempotent(self):
        src = (
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\n"
            'import "@openzeppelin/contracts/utils/Pausable.sol";\n'
            "contract C is Ownable { constructor() Ownable(msg.sender) {} function f() public view returns(uint){return now;} }\n"
        )
        once = self.r.repair_file("C.sol", src).content
        twice = self.r.repair_file("C.sol", once)
        assert twice.content == once
        assert twice.fixes == []

    def test_non_solidity_unchanged(self):
        res = self.r.repair_file("app/main.py", "x = now\n")
        assert res.content == "x = now\n"
        assert res.fixes == []

    def test_repair_then_verify_resolves_static_failures(self):
        v = CodeVerifier(enable_solc=False)
        src = "contract C { function f(bytes memory b) public pure returns (uint){ return b.length(); } }\n"
        before = v.verify("C.sol", src)
        assert before.status == VerificationStatus.FAILED
        repaired = self.r.repair_file("C.sol", src).content
        after = v.verify("C.sol", repaired)
        assert after.status != VerificationStatus.FAILED


class TestOwnableBaseCallScanner:
    """The Ownable removal must never corrupt valid Solidity (review must-fix)."""

    def test_nested_parens_fully_removed(self):
        out, n = _strip_ownable_base_call("constructor() Ownable(_msgSender()) {}")
        assert n == 1
        assert out == "constructor()  {}"  # no dangling ')'

    def test_new_instantiation_preserved(self):
        out, n = _strip_ownable_base_call("x = new Ownable(msg.sender);")
        assert n == 0
        assert "new Ownable(msg.sender)" in out

    def test_cast_preserved(self):
        out, n = _strip_ownable_base_call("address o = Ownable(token).owner();")
        assert n == 0
        assert "Ownable(token).owner()" in out

    def test_inheritance_untouched(self):
        out, n = _strip_ownable_base_call("contract C is Ownable {}")
        assert n == 0

    def test_identifier_suffix_not_matched(self):
        out, n = _strip_ownable_base_call("x = MyOwnable(1);")
        assert n == 0

    def test_only_ownable_removed_among_base_calls(self):
        out, n = _strip_ownable_base_call("constructor() Ownable(msg.sender) ReentrancyGuard() {}")
        assert n == 1
        assert "ReentrancyGuard()" in out
        assert "Ownable(" not in out

    def test_base_call_at_segment_start_is_removed(self):
        # A code segment can begin with `Ownable(` (e.g. right after a comment);
        # idx == 0 must still count as a clean left boundary.
        out, n = _strip_ownable_base_call("Ownable(msg.sender) {}")
        assert n == 1
        assert out == " {}"


class TestLengthEnumerableGuard:
    """`.length()` must not be rewritten when Enumerable* libraries are used."""

    def setup_method(self):
        self.r = CodeRepairer()

    def test_enumerable_length_preserved(self):
        src = (
            "pragma solidity ^0.8.20;\n"
            'import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";\n'
            "contract C {\n"
            "  using EnumerableSet for EnumerableSet.AddressSet;\n"
            "  EnumerableSet.AddressSet private s;\n"
            "  function n() public view returns (uint) { return s.length(); }\n"
            "}\n"
        )
        res = self.r.repair_file("C.sol", src)
        assert "s.length()" in res.content

    def test_enumerable_length_not_flagged_by_verifier(self):
        v = CodeVerifier(enable_solc=False)
        src = (
            "pragma solidity ^0.8.20;\n"
            "contract C {\n"
            "  using EnumerableSet for EnumerableSet.AddressSet;\n"
            "  function n() public view returns (uint) { return s.length(); }\n"
            "}\n"
        )
        assert v.verify("C.sol", src).status != VerificationStatus.FAILED

    def test_plain_array_length_still_fixed(self):
        src = (
            "pragma solidity ^0.8.20;\n"
            "contract C { function f(uint[] memory a) public pure returns (uint){ return a.length(); } }\n"
        )
        res = self.r.repair_file("C.sol", src)
        assert "a.length()" not in res.content


class TestOzImportAnchoring:
    def test_only_import_lines_rewritten(self):
        src = (
            'import "@openzeppelin/contracts/utils/Pausable.sol";\n'
            'string x = "@openzeppelin/contracts/utils/Pausable.sol";\n'
        )
        out, n = _normalize_oz_import_paths(src)
        assert n == 1  # only the import directive
        assert (
            'security/Pausable.sol";\nstring x = "@openzeppelin/contracts/utils/Pausable.sol' in out
        )


class TestUnterminatedStringSafety:
    def test_unterminated_string_does_not_swallow_rest_of_file(self):
        # The bad string is on its own line; fixes after it must still apply.
        r = CodeRepairer()
        src = (
            "pragma solidity ^0.8.20;\n"
            'string bad = "oops;\n'
            "contract C { function f() public view returns (uint){ return now; } }\n"
        )
        res = r.repair_file("C.sol", src)
        assert "block.timestamp" in res.content


class TestEnsureContractDependencies:
    def _pkg(self, deps=None):
        body = {"name": "contracts", "devDependencies": {"hardhat": "^2.19.0"}}
        if deps is not None:
            body["dependencies"] = deps
        return _File("contracts/package.json", json.dumps(body, indent=2) + "\n")

    def _sol(self):
        return _File(
            "contracts/contracts/M.sol",
            'import "@openzeppelin/contracts/access/Ownable.sol";\ncontract M is Ownable {}',
        )

    def test_injects_oz_when_imported(self):
        pkg = self._pkg()
        fixes = ensure_contract_dependencies([pkg, self._sol()])
        data = json.loads(pkg.content)
        assert data["dependencies"][OZ_PACKAGE] == OZ_VERSION
        assert fixes and OZ_PACKAGE in fixes[0]

    def test_noop_when_no_oz_import(self):
        pkg = self._pkg()
        before = pkg.content
        plain = _File("contracts/contracts/M.sol", "pragma solidity ^0.8.20;\ncontract M {}")
        fixes = ensure_contract_dependencies([pkg, plain])
        assert fixes == []
        assert pkg.content == before

    def test_idempotent_when_already_present(self):
        pkg = self._pkg(deps={OZ_PACKAGE: OZ_VERSION})
        fixes = ensure_contract_dependencies([pkg, self._sol()])
        assert fixes == []

    def test_skips_when_no_package_json(self):
        # OZ imported but no package.json in the set -> no crash, no fix.
        fixes = ensure_contract_dependencies([self._sol()])
        assert fixes == []

    def test_invalid_json_is_handled_gracefully(self):
        bad = _File("contracts/package.json", "{ not valid json ")
        fixes = ensure_contract_dependencies([bad, self._sol()])
        assert fixes == []
        assert bad.content == "{ not valid json "
