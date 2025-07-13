import asyncpg
import os
import socket
from dotenv import load_dotenv
import logging
import asyncio
import urllib.parse

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),  # Save logs to a file
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

async def test_connection():
    load_dotenv()
    db_url = os.getenv("SUPABASE_DB_URL")
    
    if not db_url:
        logger.error("SUPABASE_DB_URL environment variable is not set")
        return
    
    logger.info(f"Attempting to connect with SUPABASE_DB_URL: {db_url}")
    
    # Parse the URL to extract components for debugging
    try:
        parsed_url = urllib.parse.urlparse(db_url)
        hostname = parsed_url.hostname
        port = parsed_url.port
        username = parsed_url.username
        database = parsed_url.path.lstrip('/')
        logger.debug(f"Parsed URL - Hostname: {hostname}, Port: {port}, Username: {username}, Database: {database}")
    except Exception as e:
        logger.error(f"Failed to parse SUPABASE_DB_URL: {str(e)}")
        return
    
    # Test DNS resolution
    try:
        socket.getaddrinfo(hostname, port)
        logger.debug(f"DNS resolution successful for {hostname}:{port}")
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {hostname}:{port} - {str(e)}")
        return
    
    # Test connection
    try:
        conn = await asyncpg.connect(db_url)
        server_version = await conn.fetchval("SELECT version();")
        logger.info(f"Connection successful! Server version: {server_version}")
        await conn.close()
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}", exc_info=True)
        logger.debug(f"Full exception traceback: {str(e.__traceback__)}")

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}", exc_info=True)