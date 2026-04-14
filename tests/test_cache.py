"""Tests for engine.cache.GitSageCache."""

from pathlib import Path

from engine.cache import GitSageCache
from engine.models import CommitResult


def _result(msg: str = "feat: test", files: list | None = None) -> CommitResult:
    return CommitResult(
        message=msg,
        explanation="🧠 What changed:\n- something\n💡 Why it matters:\ntest\n🎯 Scope:\ntest.py",
        confidence_score=0.9,
        files_changed=files or ["test.py"],
    )


def test_cache_save_and_get(tmp_path: Path):
    cache = GitSageCache(cache_path=tmp_path / ".test_cache")
    diff = "test diff content"
    result = _result("feat: Add new feature", ["main.py"])

    cache.save(diff, result)
    cached = cache.get(diff)

    assert cached is not None
    assert cached.message == result.message
    assert cached.confidence_score == result.confidence_score
    assert cached.files_changed == result.files_changed


def test_cache_miss(tmp_path: Path):
    cache = GitSageCache(cache_path=tmp_path / ".test_cache_miss")
    assert cache.get("non-existent diff") is None


def test_cache_miss_before_file_created(tmp_path: Path):
    cache = GitSageCache(cache_path=tmp_path / "does_not_exist")
    assert cache.get("anything") is None


def test_cache_fifo_limit(tmp_path: Path):
    cache = GitSageCache(cache_path=tmp_path / ".test_fifo")

    # Fill beyond the 100-entry cap
    for i in range(105):
        cache.save(f"diff {i}", _result(f"msg {i}"))

    # Earliest entries should have been evicted
    assert cache.get("diff 0") is None
    assert cache.get("diff 4") is None

    # Most recent entries survive
    assert cache.get("diff 104") is not None
    assert cache.get("diff 100") is not None


def test_cache_overwrite_same_diff(tmp_path: Path):
    cache = GitSageCache(cache_path=tmp_path / ".test_overwrite")
    diff = "same diff"

    cache.save(diff, _result("feat: first"))
    cache.save(diff, _result("feat: second"))

    cached = cache.get(diff)
    assert cached is not None
    assert cached.message == "feat: second"


def test_cache_clear(tmp_path: Path):
    path = tmp_path / ".test_clear"
    cache = GitSageCache(cache_path=path)
    cache.save("some diff", _result())

    assert path.exists()
    cache.clear()
    assert not path.exists()
    assert cache.get("some diff") is None


def test_cache_corrupt_file_returns_none(tmp_path: Path):
    path = tmp_path / ".corrupt_cache"
    path.write_text("NOT VALID JSON")

    cache = GitSageCache(cache_path=path)
    assert cache.get("any diff") is None
