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
        logging.FileHandler("test_chat.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base URLs
HTTP_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

# Admin credentials (replace with existing admin user)
ADMIN_CREDENTIALS = {
    "email": "admin@example.com",
    "password": "SecurePass123!"
}

# Test messages
TEST_MESSAGES = [
    "What is the campaign's stance on economic policy?",
    "Tell me about the uploaded documents."
]

async def test_chat():
    try:
        # Login to get JWT token
        logger.debug(f"Sending POST /auth/login with payload: {json.dumps(ADMIN_CREDENTIALS, indent=2)}")
        response = requests.post(f"{HTTP_BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
        logger.info(f"POST /auth/login - Status: {response.status_code}, Response: {response.text}")
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info(f"Login token: {token}")

        # Connect to WebSocket
        async with websockets.connect(f"{WS_BASE_URL}/chat/ws") as websocket:
            # Send JWT token
            await websocket.send(token)
            logger.debug(f"Sent JWT token: {token}")

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
        logger.error(f"Chat test failed: {str(e)}", exc_info=True)

def run_tests():
    asyncio.run(test_chat())

if __name__ == "__main__":
    run_tests()