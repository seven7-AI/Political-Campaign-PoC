import os
from resend import Resend
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("email_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        load_dotenv()
        self.client = Resend(api_key=os.getenv("RESEND_API_KEY"))
        if not self.client.api_key:
            logger.error("RESEND_API_KEY not set")
            raise ValueError("Resend API key missing")
        logger.info("Resend client initialized")

    async def send_notification(self, to_email: str, subject: str, message: str):
        try:
            email = os.getenv("EMAIL")
            email_data = {
                "from": email,  # Replace with your verified domain
                "to": to_email,
                "subject": subject,
                "html": f"<p>{message}</p>"
            }
            response = self.client.emails.send(email_data)
            logger.info(f"Sent email to {to_email}: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            raise