import sys
from ezstools.string_tools import sort_by_similitude

def get_menu_input(
        zero_option_text: str,
        prompt: str,
        options: list[str],
        space_separated: bool = False,
) -> int | tuple[int, ...]:
    """
    Gets a valid user input from a menu

    Accept both options and index as responses.

    If space_separated is True, it will allow the user to input multiple options separated by spaces. and will return an tuple of selected options.
    """
    print(zero_option_text)
    for index, option in enumerate(options, start=1):
        print(f"[ {index} ]\t{option}")

    while True:
        try:
            selection = input(prompt)

            if not selection:
                print("That's not it.")
                continue

            # if the input is a number, check if it's within the range of options
            if selection.isdigit():
                selection = int(selection)
                if 0 <= selection <= len(options):
                    return selection
                else:
                    print("Invalid option. Please select a valid number.")
           
            # If the input is a string, check if it matches any option
            elif isinstance(selection, str):

                if space_separated:
                    # Split the input by spaces and check each part its a valid index
                    selection = selection.strip().lower().split()
                    matched_options = []

                    for part in selection:
                        if part.isdigit():
                            part = int(part)
                            if 0 < part <= len(options):
                                matched_options.append(part) # Convert to zero-based index
                        else:
                            # skip if the part is not a digit
                            print(f"\t [ ! ]\t{part} is not a valid option and therefore will be ignored.")

                    selection = tuple(matched_options)
                        
                else:
                    # Sort options by similarity to the input
                    selection = sort_by_similitude(selection.strip().lower(), options, case_sensitive=False)[-1]

                    # map selection to its index
                    selection = options.index(selection) + 1 if selection in options else None

                    # This shouldnt ever happen, but just in case
                    if selection is None:
                        print("[ FATAL ]\tSelection not found in options. SHOULD NEVER HAPPEN.")
                        sys.exit(1)

            else:
                print("Can't understand that input >u<")
                continue

            # Flush the input buffer
            sys.stdin.flush()
            print("\n\n") # some spacing for clarity
            return selection

        except ValueError:
            print("Invalid input. Please enter a number.")



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