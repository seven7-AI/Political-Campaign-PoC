import requests
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_document.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base URL for FastAPI server
BASE_URL = "http://localhost:8000"

# Admin credentials (replace with an existing admin user)
ADMIN_CREDENTIALS = {
    "email": os.getenv(ADMIN_EMAIL),
    "password": os.getenv(ADMIN_PASSWORD)
}

# Path to test PDF
PDF_PATH = r"D:\777\Political-Campaign-PoC\data\pdfs\president-trump-platinum-plan-final-version.pdf"

def login_admin():
    """Log in as admin to get JWT token"""
    try:
        logger.debug(f"Sending POST /auth/login with payload: {ADMIN_CREDENTIALS}")
        response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
        logger.info(f"POST /auth/login - Status: {response.status_code}, Response: {response.text}")
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Admin login failed: {str(e)}", exc_info=True)
        raise

def test_upload_pdf(token):
    """Test POST /document/upload"""
    try:
        if not os.path.exists(PDF_PATH):
            raise FileNotFoundError(f"PDF not found at {PDF_PATH}")
        with open(PDF_PATH, "rb") as file:
            files = {"file": (os.path.basename(PDF_PATH), file, "application/pdf")}
            headers = {"Authorization": f"Bearer {token}"}
            logger.debug(f"Sending POST /document/upload with file: {os.path.basename(PDF_PATH)}")
            response = requests.post(f"{BASE_URL}/document/upload", files=files, headers=headers)
            logger.info(f"POST /document/upload - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"POST /document/upload failed: {str(e)}", exc_info=True)
        raise

def run_tests():
    """Run all document endpoint tests"""
    try:
        logger.info("Starting test: Admin login")
        token = login_admin()
        logger.info(f"Admin token: {token}")

        logger.info("Starting test: Upload PDF")
        upload_response = test_upload_pdf(token)
        logger.info(f"Upload response: {upload_response}")

        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_tests()