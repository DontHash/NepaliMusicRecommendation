"""Hermetic tests for chunked window construction."""

from __future__ import annotations

from music_rec.embeddings import _windows_from_content


def test_windows_cover_all_tokens_with_stride_overlap():
    content = list(range(100))
    windows = _windows_from_content(content, max_length=48, stride=24, n_special=2)
    # W=46 content tokens per window, step=22 -> starts 0,22,44,66 (the 5th start
    # would be fully covered by the 4th window, so HF-style overflow stops at 4).
    assert len(windows) == 4
    assert len(windows[0]) == 46 and len(windows[-1]) == 34
    covered = set().union(*(set(window) for window in windows))
    assert covered == set(content)
    assert windows[0][22:46] == windows[1][0:24]
    assert windows[2][22:46] == windows[3][0:24]


def test_windows_short_text_is_single_window():
    assert _windows_from_content([1, 2, 3], max_length=48, stride=24, n_special=2) == [[1, 2, 3]]


def test_windows_zero_stride_no_overlap():
    windows = _windows_from_content(list(range(10)), max_length=5, stride=0, n_special=0)
    assert windows == [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]


def test_windows_expected_count_for_long_text():
    # 2814-token text with 48/24 -> ~117 content windows, not 2
    windows = _windows_from_content(list(range(2814)), max_length=48, stride=24, n_special=2)
    assert len(windows) > 100
