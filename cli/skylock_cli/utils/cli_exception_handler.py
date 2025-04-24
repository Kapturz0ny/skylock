"""
Module to handle API exceptions and display them to the user using the typer library.
"""

import typer
from rich.console import Console
from rich.traceback import Traceback
from httpx import ConnectError
from skylock_cli.exceptions import api_exceptions, core_exceptions, gmail_exceptions

err_console = Console(stderr=True)


def handle_standard_errors(error_dict: dict, status_code: int) -> None:
    """A function to handle standard API errors and raise the appropriate exception."""
    if status_code in error_dict:
        raise error_dict[status_code]


class CLIExceptionHandler:
    """A context manager to handle exceptions and display them to the user using typer"""

    def __enter__(self): ...

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Exit the runtime context related to this object.

        Args:
            exc_type (type): The exception type.
            exc_value (Exception): The exception instance.
            exc_traceback (traceback): The traceback object.

        Returns:
            bool: False if an exception was handled, otherwise None.
        """
        if isinstance(
            exc_value,
            (
                api_exceptions.SkyLockAPIError,
                core_exceptions.SkyLockCoreError,
                gmail_exceptions.GmailError,
            ),
        ):
            err_console.print(f"[red]{exc_value}[/red]")
            raise typer.Exit(code=1)
        if isinstance(exc_value, ConnectError):
            err_console.print(
                "[red]The server is not reachable at the moment. Please try again later.[/red]"
            )
            raise typer.Exit(code=1)
        if exc_type is not None:
            tb = Traceback.from_exception(
                exc_type, exc_value, exc_traceback, max_frames=5
            )
            err_console.print(tb)
            raise typer.Exit(code=1)

        return False
