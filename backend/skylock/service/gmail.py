import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.auth import exceptions
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]
from dotenv import load_dotenv
from skylock.config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
from skylock.utils.exceptions import (
    EmailAuthenticationError,
    EmailServiceUnavailable,
)
from skylock.utils.logger import logger

load_dotenv()

SCOPES = ["https://mail.google.com/"]


def get_access_token() -> Credentials:
    """Retrieves or refreshes Google API access credentials.

    Returns:
        Credentials: Google API credentials.
    """
    creds = Credentials.from_authorized_user_info(
        {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
        SCOPES,
    )
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleAuthRequest())

    return creds


def send_mail(to_email: str, subject: str, body: str) -> None:
    """Sends an email using the Gmail API.

    Args:
        to_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body content (HTML).

    Raises:
        EmailAuthenticationError: If Gmail API authentication fails.
        EmailServiceUnavailable: If sending email fails unexpectedly.
    """
    try:
        creds = get_access_token()

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)

        message = MIMEMultipart()
        message["To"] = to_email
        message["From"] = "skylock.zprp@gmail.com"
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        send_message = (
            service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        )
        logger.info(f"Message sent successfully, message ID: {send_message['id']}")

    except exceptions.RefreshError as e:
        logger.error("Authentication with Gmail API failed.")
        raise EmailAuthenticationError("Authentication with Gmail API failed.") from e
    except Exception as error:
        logger.error(f"Failed to send email: {error}")
        raise EmailServiceUnavailable("Failed to send email due to an unexpected error.") from error
