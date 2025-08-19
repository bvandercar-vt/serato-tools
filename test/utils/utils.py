import io
from contextlib import redirect_stdout
from typing import Callable


def get_print_val(func: Callable):
    captured_output = io.StringIO()
    with redirect_stdout(captured_output):
        func()
    output = captured_output.getvalue()
    return output
