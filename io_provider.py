from typing import Callable, Tuple
from typing import Callable, Optional

from input_buffer import InputBuffer


class IOProvider:
    """
    Singleton class that stores:
     - input -- Callable[[str], str]
    - output -- Callable[[str], None]

    # This class is the IO chameleon: it lets the core logic talk to any UI (console, web, etc) without knowing or caring.
    # It also lets you swap input/output on the fly, so you can automate, test, or just be fancy.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IOProvider, cls).__new__(cls)
            cls._instance.input_fn = None
            cls._instance.output_fn = None
        return cls._instance

    def _set_input_wrapper(self, input_fn: Callable[[str], str]) -> Callable[[str], str]:
        """
        Wrapper for the input function to give priority to the input buffer.
        Checks (and consumes) the input buffer on EACH call.
        # This is the secret sauce: if there's a value in the buffer, use it instead of asking the user. Great for automation and web UI!
        """
        def wrapped_input( prompt: str):

            prompt = prompt or "Provide a valid input: "

            v = InputBuffer().pop()
            if v is not None:
                return v
            return input_fn(prompt)
        return wrapped_input

    def set_io(
        self, input_fn: Callable[[str], str], output_fn: Callable[[str], None]
    ) -> None:
        self.input_fn = self._set_input_wrapper(input_fn)
        self.output_fn = output_fn
        # This lets you swap input/output at runtime, so the same logic works everywhere (and you can test things easily).

    def get_io(self) -> Tuple[Callable[[str], str], Callable[[str], None]]:
        if not callable(self.input_fn) or not callable(self.output_fn):
            raise RuntimeError("Input or output function not set.")

        return self.input_fn, self.output_fn

    def get_input(self) -> Callable[[str], str]:
        if not callable(self.input_fn):
            raise RuntimeError("Input function not set.")
        return self.input_fn

    def get_output(self) -> Callable[[str], None]:
        if not callable(self.output_fn):
            raise RuntimeError("Output function not set.")
        return self.output_fn

    def set_input(self, input_fn: Callable[[str], str]) -> None:
        self.input_fn = self._set_input_wrapper(input_fn)

    def set_output(self, output_fn: Callable[[str], None]) -> None:
        self.output_fn = output_fn