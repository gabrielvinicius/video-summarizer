# src/notifications/infrastructure/sms_adapter.py
import logging

logger = logging.getLogger(__name__)

class SmsAdapter:
    def __init__(self, account_sid: str = "", auth_token: str = ""):
        # In a real scenario, these would be configured via settings
        self.account_sid = account_sid
        self.auth_token = auth_token

    async def send(self, to: str, message: str) -> None:
        """Placeholder for sending an SMS notification."""
        if not self.account_sid or not self.auth_token:
            logger.warning("SmsAdapter is not configured.")
            return

        logger.info(f"[SmsAdapter] Pretending to send SMS to {to}: {message}")
        # In a real implementation, you would use a library like twilio
        # from twilio.rest import Client
        # client = Client(self.account_sid, self.auth_token)
        # client.messages.create(to=to, from_="your_twilio_number", body=message)
        pass
