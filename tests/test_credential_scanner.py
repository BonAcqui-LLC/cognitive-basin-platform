import json
from pathlib import Path

from tools.ci.scan_credentials import scan_files


POLICY_PATH = Path("ops/policies/credential-scan-policy.json")


def _policy():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_short_sk_substrings_and_provenance_mentions_are_not_credentials(tmp_path):
    (tmp_path / "safe.md").write_text(
        "risk-sensitive evidence and ALL_TOKENS_KEYS_FOR_GROK were excluded",
        encoding="utf-8",
    )
    policy = _policy()
    assert scan_files(
        ["safe.md"],
        policy["prohibited"],
        policy["prohibited_paths"],
        root=tmp_path,
    ) == []


def test_plausible_secret_content_is_rejected(tmp_path):
    (tmp_path / "unsafe.txt").write_text(
        "sk-" + ("a" * 32),
        encoding="utf-8",
    )
    policy = _policy()
    matches = scan_files(
        ["unsafe.txt"],
        policy["prohibited"],
        policy["prohibited_paths"],
        root=tmp_path,
    )
    assert matches == [
        ("unsafe.txt", "content", "sk-[A-Za-z0-9_-]{20,}")
    ]


def test_forbidden_token_filename_is_rejected_even_when_content_is_safe(tmp_path):
    file_name = "archive/ALL_TOKENS_KEYS_FOR_GROK.txt"
    target = tmp_path / file_name
    target.parent.mkdir()
    target.write_text("redacted", encoding="utf-8")
    policy = _policy()
    matches = scan_files(
        [file_name],
        policy["prohibited"],
        policy["prohibited_paths"],
        root=tmp_path,
    )
    assert matches == [
        (file_name, "path", "ALL_TOKENS_KEYS_FOR_GROK")
    ]
