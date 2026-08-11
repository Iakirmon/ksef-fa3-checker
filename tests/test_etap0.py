"""Placeholder — testy pojawią się od etapu 1."""


def test_repo_ma_korpus_provenance() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert (root / "korpus" / "PROVENANCE.md").is_file()
