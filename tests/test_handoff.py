import websockets
import asyncio
import requests
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_handoff.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base URLs
HTTP_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

# User credentials (replace with existing user)
USER_CREDENTIALS = {
    "email": "volunteer_test_8478b3ba@mailinator.com",
    "password": "SecurePass123!"
}

# Test messages
TEST_MESSAGES = [
    "What is the campaign's economic policy?",
    "I need to talk to a person about volunteering."
]

async def test_handoff():
    try:
        # Login to get JWT token
        logger.debug(f"Sending POST /auth/login with payload: {json.dumps(USER_CREDENTIALS, indent=2)}")
        response = requests.post(f"{HTTP_BASE_URL}/auth/login", json=USER_CREDENTIALS)
        logger.info(f"POST /auth/login - Status: {response.status_code}, Response: {response.text}")
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info(f"Login token: {token}")

        # Connect to WebSocket
        async with websockets.connect(f"{WS_BASE_URL}/chat/ws") as websocket:
            # Send JWT token
            await websocket.send(token)
            logger.debug(f"Sent JWT token: {token}")

            # Check for session resumption
            session_response = await websocket.recv()
            logger.info(f"Session response: {session_response}")

            # Send test messages
            for message in TEST_MESSAGES:
                logger.debug(f"Sending message: {message}")
                await websocket.send(message)
                response = await websocket.recv()
                logger.info(f"Received response: {response}")

            # Close WebSocket
            await websocket.close()
            logger.info("WebSocket closed")

    except Exception as e:
        logger.error(f"Handoff test failed: {str(e)}", exc_info=True)

def run_tests():
    asyncio.run(test_handoff())

if __name__ == "__main__":
    run_tests()