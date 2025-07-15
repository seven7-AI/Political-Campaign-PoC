import requests
import logging
import json
from uuid import uuid4
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_auth.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")
VOLUNTEER_EMAIL = os.getenv("VOLUNTEER_EMAIL")
VOLUNTEER_PASSWORD = os.getenv("VOLUNTEER_PASSWORD")

# Base URL for FastAPI server
BASE_URL = "http://localhost:8000"

# Sample user data
USER_DATA = {
    "email": VOLUNTEER_EMAIL,
    "password": VOLUNTEER_PASSWORD,
    "role": "volunteer",
    "location": "Boston"
}

# Sample profile update data
UPDATE_DATA = {
    "location": "New York"
}

# Sample questionnaire responses
QUESTIONNAIRE_DATA = [
    {"question_id": 1, "answer": "I support progressive taxation to fund social programs."},
    {"question_id": 2, "answer": "Healthcare and education should be accessible to all."},
    {"question_id": 3, "answer": "Prioritize renewable energy to combat climate change."},
    {"question_id": 4, "answer": "Diplomacy should guide international relations."},
    {"question_id": 5, "answer": "I’m motivated by social justice and community impact."}
]

def test_register():
    """Test POST /auth/register"""
    try:
        logger.debug(f"Sending POST /auth/register with payload: {json.dumps(USER_DATA, indent=2)}")
        response = requests.post(f"{BASE_URL}/auth/register", json=USER_DATA)
        logger.info(f"POST /auth/register - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"POST /auth/register failed: {str(e)}", exc_info=True)
        raise

def test_login():
    """Test POST /auth/login"""
    try:
        login_data = {"email": USER_DATA["email"], "password": USER_DATA["password"]}
        logger.debug(f"Sending POST /auth/login with payload: {json.dumps(login_data, indent=2)}")
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        logger.info(f"POST /auth/login - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"POST /auth/login failed: {str(e)}", exc_info=True)
        raise

def test_get_profile(token):
    """Test GET /auth/profile"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        logger.debug(f"Sending GET /auth/profile with headers: {headers}")
        response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
        logger.info(f"GET /auth/profile - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"GET /auth/profile failed: {str(e)}", exc_info=True)
        raise

def test_update_profile(token):
    """Test PUT /auth/profile"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        logger.debug(f"Sending PUT /auth/profile with headers: {headers}, payload: {json.dumps(UPDATE_DATA, indent=2)}")
        response = requests.put(f"{BASE_URL}/auth/profile", json=UPDATE_DATA, headers=headers)
        logger.info(f"PUT /auth/profile - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"PUT /auth/profile failed: {str(e)}", exc_info=True)
        raise

def test_submit_questionnaire(token):
    """Test POST /auth/volunteer/questionnaire"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        logger.debug(f"Sending POST /auth/volunteer/questionnaire with headers: {headers}, payload: {json.dumps(QUESTIONNAIRE_DATA, indent=2)}")
        response = requests.post(f"{BASE_URL}/auth/volunteer/questionnaire", json=QUESTIONNAIRE_DATA, headers=headers)
        logger.info(f"POST /auth/volunteer/questionnaire - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"POST /auth/volunteer/questionnaire failed: {str(e)}", exc_info=True)
        raise

def test_get_questionnaire(token):
    """Test GET /auth/volunteer/questionnaire"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        logger.debug(f"Sending GET /auth/volunteer/questionnaire with headers: {headers}")
        response = requests.get(f"{BASE_URL}/auth/volunteer/questionnaire", headers=headers)
        logger.info(f"GET /auth/volunteer/questionnaire - Status: {response.status_code}, Headers: {response.headers}, Response: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"GET /auth/volunteer/questionnaire failed: {str(e)}", exc_info=True)
        raise

def run_tests():
    """Run all endpoint tests"""
    try:
        # Test registration
        logger.info("Starting test: Register user")
        register_response = test_register()
        logger.info(f"Register response: {register_response}")

        # Test login
        logger.info("Starting test: Login user")
        login_response = test_login()
        token = login_response["access_token"]
        logger.info(f"Login token: {token}")

        # Test get profile
        logger.info("Starting test: Get profile")
        profile_response = test_get_profile(token)
        logger.info(f"Profile response: {profile_response}")

        # Test update profile
        logger.info("Starting test: Update profile")
        update_response = test_update_profile(token)
        logger.info(f"Update profile response: {update_response}")

        # Test submit questionnaire
        logger.info("Starting test: Submit questionnaire")
        questionnaire_response = test_submit_questionnaire(token)
        logger.info(f"Questionnaire response: {questionnaire_response}")

        # Test get questionnaire
        logger.info("Starting test: Get questionnaire")
        get_questionnaire_response = test_get_questionnaire(token)
        logger.info(f"Get questionnaire response: {get_questionnaire_response}")

        logger.info("All tests completed successfully")
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_tests()