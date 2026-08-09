"""Pluggable email sending. ConsoleEmailService is the development default — it logs
the email instead of sending it. Swap in a Brevo/Resend-backed implementation once
Phase 3 wires up real email (SRS section 17); nothing that calls get_email_service()
needs to change."""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("attachify.email")


class EmailService(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email. Implementations decide how."""


class ConsoleEmailService(EmailService):
    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("EMAIL to=%s subject=%r\n%s", to, subject, body)


def get_email_service() -> EmailService:
    return ConsoleEmailService()
