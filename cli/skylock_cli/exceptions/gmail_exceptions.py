"""
Module for exceptions raised by the Gmail service.
"""

class GmailError(Exception):
    """Base exception for Gmail service errors.

    Args:
        message (Optional[str]): The error message associated with the exception.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmailServiceUnavailableError(GmailError):
    """Exception raised when the email service is unavailable."""

    def __init__(self) -> None:
        message = "Email service is unavailable. Please try to register again later."
        super().__init__(message)
        
