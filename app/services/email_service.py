import os
import resend
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
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            logger.error("RESEND_API_KEY not set")
            raise ValueError("Resend API key missing")

        # Set the API key for the resend module
        resend.api_key = resend_api_key
        logger.info("Resend client initialized")

    async def send_notification(self, to_email: str, subject: str, message: str):
        try:
            email = os.getenv("EMAIL")
            params = {
                "from": email,  # Replace with your verified domain
                "to": [to_email],
                "subject": subject,
                "html": f"<p>{message}</p>"
            }
            response = resend.Emails.send(params)
            logger.info(f"Sent email to {to_email}: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            raise
