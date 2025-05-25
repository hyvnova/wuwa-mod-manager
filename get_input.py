from re import A
import sys
from typing import List, Tuple, Union
from ezstools.string_tools import sort_by_similitude


def get_menu_input(
    zero_option_text: str,
    prompt: str,
    options: List[str],
    space_separated: bool = False,
) -> Union[int, Tuple[int, ...]]:
    """
    Ask the user to pick from *options*.
    The caller decides whether multiple picks are allowed (``space_separated``).

    • If the user types **numbers** → those numbers are taken as 1-based indexes
      (0 is the special “zero option”).
    • If the user types **text** → we fuzzy-match each token against the option list
      with ``sort_by_similitude`` and take the closest hit.

    Returns
    -------
    int
        a single index (when ``space_separated=False``)
    tuple[int, ...]
        many indexes in input order with duplicates removed
    """

    print(zero_option_text)
    for idx, opt in enumerate(options, start=1):
        print(f"[ {idx} ]\t{opt}")

    def _match_token(token: str) -> int | None:
        """Return 1-based index for a textual token (best fuzzy match) or None."""
        token = token.strip().lower()
        if not token:
            return None
        best = sort_by_similitude(token, options, case_sensitive=False)[-1]
        return options.index(best) + 1 if best in options else None

    while True:
        raw = input(prompt).strip()
        if not raw:
            print("That's not it.")
            continue

        # Split once if multi-select, otherwise keep as single token
        tokens = raw.split() if space_separated else [raw]

        indices: List[int] = []
        for tok in tokens:
            if tok.isdigit():
                num = int(tok)
                if 0 <= num <= len(options):
                    indices.append(num)
                else:
                    print(f"\t[ ! ] {num} is out of range and will be ignored.")
            else:
                match = _match_token(tok)
                if match is None:
                    print(f"\t[ ! ] '{tok}' not recognised; ignored.")
                else:
                    indices.append(match)

        # drop duplicates while keeping order
        seen: set[int] = set()
        indices = [i for i in indices if not (i in seen or seen.add(i))]

        if not indices:
            print("No valid selection made.")
            continue

        # Flush any stray buffered input (Windows quirk guard)
        try:
            sys.stdin.flush()
        except AttributeError:
            pass  # not all platforms supply flush()

        print("\n")
        if space_separated:
            return tuple(indices)
        return indices[0]


def get_confirmation(
        prompt: str = "Are you sure? [y/n]: ",
        default: str = "n",
) -> bool:
    """
    Gets a confirmation from the user
    """
    while True:
        response = input(prompt).strip().lower()
        if not response:
            response = default

        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
