from typing import Callable, Tuple, Optional

from input_buffer import InputBuffer


class IOProvider:
    """Singleton for pluggable input/output callables.

    - input:  Callable[[str], str]
    - output: Callable[[str], None]

    The input function is wrapped to consult an InputBuffer first, enabling
    non-blocking automation (used by the Web UI and tests) while keeping the
    same code paths for the console UI.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IOProvider, cls).__new__(cls)
            cls._instance.input_fn = None
            cls._instance.output_fn = None
        return cls._instance

    def _set_input_wrapper(self, input_fn: Callable[[str], str]) -> Callable[[str], str]:
        """Wrap the input function to give priority to the InputBuffer."""
        def wrapped_input(prompt: str):
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
        # Allows swapping IO at runtime (console/web/tests).

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
