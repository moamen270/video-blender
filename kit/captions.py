"""Caption formatting and grouping helper (Task G5)."""
from __future__ import annotations

import string
from typing import Any, Iterable


def groups(
    words: list[dict[str, Any]],
    start_frame: int,
    fps: float | int = 24,
    *,
    max_words: int = 3,
    max_chars: int = 16,
    keywords: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Split word timings into caption groups.

    Args:
        words: List of word dicts or objects with 'w', 'start', 'end'.
        start_frame: Starting frame of the line speech.
        fps: Frames per second (default 24).
        max_words: Maximum words per caption group (default 3).
        max_chars: Maximum characters per caption group (default 16).
        keywords: Words that trigger highlight (hi=True).

    Returns:
        List of dicts with 'start_frame', 'end_frame', 'text', 'hi'.
    """
    if not words:
        return []

    def get_w(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("w", item.get("text", "")))
        return str(getattr(item, "w", getattr(item, "text", "")))

    def get_start(item: Any) -> float:
        if isinstance(item, dict):
            return float(item["start"])
        return float(item.start)

    def get_end(item: Any) -> float:
        if isinstance(item, dict):
            return float(item["end"])
        return float(item.end)

    word_groups: list[list[Any]] = []
    curr: list[Any] = []

    for w in words:
        w_text = get_w(w)
        if curr:
            cand = " ".join([get_w(x) for x in curr] + [w_text])
            if len(cand) > max_chars:
                word_groups.append(curr)
                curr = []

        curr.append(w)

        if len(curr) >= max_words or w_text.endswith((".", "?", "!", ",")):
            word_groups.append(curr)
            curr = []

    if curr:
        word_groups.append(curr)

    kw_set = {k.lower().strip(string.punctuation) for k in keywords}
    raw_groups: list[dict[str, Any]] = []

    for grp in word_groups:
        first = grp[0]
        last = grp[-1]
        s_frame = start_frame + round(get_start(first) * fps)
        e_frame = start_frame + round(get_end(last) * fps) + 3

        texts = [get_w(x) for x in grp]
        clean_words = [t.rstrip(",") for t in texts]
        text_str = " ".join(clean_words).upper().rstrip(",")

        hi = any(t.lower().strip(string.punctuation) in kw_set for t in texts)
        raw_groups.append({
            "start_frame": s_frame,
            "end_frame": e_frame,
            "text": text_str,
            "hi": hi,
        })

    for i in range(len(raw_groups) - 1):
        next_s = raw_groups[i + 1]["start_frame"]
        if raw_groups[i]["end_frame"] > next_s:
            raw_groups[i]["end_frame"] = next_s

    return raw_groups
