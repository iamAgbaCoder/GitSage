from engine.cache import GitSageCache
from engine.models import CommitResult


def test_cache_save_and_get(tmp_path):
    cache_file = tmp_path / ".test_cache"
    cache = GitSageCache(cache_file=str(cache_file))

    diff = "test diff content"
    result = CommitResult(
        message="feat: Add new feature",
        explanation="Added a new feature for testing.",
        confidence_score=0.95,
        files_changed=["main.py"],
    )

    # Save to cache
    cache.save(diff, result)

    # Retrieve from cache
    cached_result = cache.get(diff)

    assert cached_result is not None
    assert cached_result.message == result.message
    assert cached_result.confidence_score == result.confidence_score
    assert cached_result.files_changed == result.files_changed


def test_cache_miss(tmp_path):
    cache_file = tmp_path / ".test_cache_miss"
    cache = GitSageCache(cache_file=str(cache_file))

    assert cache.get("non-existent diff") is None


def test_cache_fifo_limit(tmp_path):
    cache_file = tmp_path / ".test_cache_fifo"
    cache = GitSageCache(cache_file=str(cache_file))

    # Fill cache beyond limit (50)
    for i in range(55):
        diff = f"diff {i}"
        result = CommitResult(
            message=f"msg {i}",
            explanation="exp",
            confidence_score=0.9,
            files_changed=[],
        )
        cache.save(diff, result)

    # Check that the first entries are gone
    assert cache.get("diff 0") is None
    assert cache.get("diff 4") is None
    # Latest entries should still be there
    assert cache.get("diff 54") is not None
