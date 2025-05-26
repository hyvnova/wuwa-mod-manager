from typing import List


def sort_by_similitude(
    target: str, options: List[str], case_sensitive: bool = True
) -> List[str]:
    """
    Sorts a list of strings by their similarity to a target string.
    Returns a list of strings sorted from most to least similar.

    Notice that this WILL it's a sort, not a discard, so all options will be returned.
    """
    percents = {}

    if not case_sensitive:
        options = [*map(lambda w: w.lower(), options)]
        target = target.lower()

    for word in options:
        similar_count: int = 0

        for word_char, target_char in zip(word, target):

            if word_char == target_char:
                similar_count += 1

        # calculate percent
        percents[word] = (similar_count * 100) / (len(word) or 1)

    return sorted(percents, key=percents.get, reverse=True) # type: ignore
