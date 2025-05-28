from typing import List, Optional
import re

# ------------------------------------------------------------
#  Normalisation helpers
# ------------------------------------------------------------
_non_alnum = re.compile(r"[^a-z0-9\s]+")


def _clean(text: str) -> str:
    """
    Lowercase, kill punctuation, collapse spaces.
    """
    return _non_alnum.sub(" ", text.lower()).split() # type: ignore


def _join_tokens(tokens) -> str:
    # Sort so word order doesn't matter (token-set ratio style)
    return " ".join(sorted(tokens))



def most_similar_option(
    target: str, options: List[str], *, cutoff: float = 0.0
) -> Optional[str]:
    """
    Return the option most similar to *target*.
    • Uses RapidFuzz’s token_set_ratio if available (best quality / speed)
    • Falls back to difflib SequenceMatcher.
    • Normalises strings: case-insensitive, ignores punctuation, order-agnostic.

    *cutoff* (0-100) – minimum similarity required, or None if no match.
    """

    # ----  Pre-process ------------------------------------------------------
    tgt_norm = _join_tokens(_clean(target))
    opts_norm = {opt: _join_tokens(_clean(opt)) for opt in options}

    try:
        # ----  RapidFuzz path ----------------------------------------------
        from rapidfuzz import fuzz, process  # noqa: WPS433 (external import inside fn)

        match, score, _ = process.extractOne(
            tgt_norm,
            opts_norm.values(),
            scorer=fuzz.token_set_ratio,
        )
        if score < cutoff:
            return None
        # reverse-lookup the original option by its normalised string
        return next(orig for orig, norm in opts_norm.items() if norm == match)

    except ModuleNotFoundError:
        # ----  Difflib fallback --------------------------------------------
        from difflib import SequenceMatcher

        def ratio(a: str, b: str) -> float:
            return SequenceMatcher(None, a, b).ratio() * 100

        scored = [(opt, ratio(tgt_norm, norm)) for opt, norm in opts_norm.items()]
        best, best_score = max(scored, key=lambda p: p[1])
        return best if best_score >= cutoff else None
