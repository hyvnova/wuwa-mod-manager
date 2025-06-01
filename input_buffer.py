"""
This is shithole fix.
This "input buffer" which it's not technically a buffer but I don't care it's a,
"priority input buffer" it holds values that will be used in the next input call.

meaning, 
if you call input() it will return the first value in the buffer, instead of waiting for user input.
"""


from typing import Any


class InputBuffer:
    """
    InputBuffer is a singleton class that holds a list of input values that have priority over user input.
    It allows you to set values that will be returned on the next input call, bypassing the need for user interaction.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InputBuffer, cls).__new__(cls)
            cls._instance.buffer = [] # type: ignore
        return cls._instance

    def push(self, *values: Any) -> None:
        """
        Push values to the input buffer.
        These values will be returned on the next input call.
        """
        self.buffer.extend(values) # type: ignore

    def pop(self) -> Any | None:
        """
        Pop the first value from the input buffer.
        If the buffer is empty, it returns None.
        """
        if not self.buffer:
            return None
        return self.buffer.pop(0)
