import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import urllib.parse

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("setup_db.log"),  # Save logs to a file
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

def setup_supabase():
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error(f"SUPABASE_URL or SUPABASE_ANON_KEY not set: URL={supabase_url}, Key={'set' if supabase_key else 'not set'}")
        return
    
    logger.info(f"Initializing Supabase client with URL: {supabase_url}")
    
    # Parse URL for debugging
    try:
        parsed_url = urllib.parse.urlparse(supabase_url)
        hostname = parsed_url.hostname
        logger.debug(f"Parsed URL - Hostname: {hostname}")
    except Exception as e:
        logger.error(f"Failed to parse SUPABASE_URL: {str(e)}")
        return
    
    # Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
        return
    
    # Verify table existence
    tables = ["profiles", "questions", "questionnaire_responses"]
    for table in tables:
        try:
            response = supabase.table(table).select("*").limit(1).execute()
            logger.info(f"Table '{table}' exists and is accessible")
        except Exception as e:
            logger.warning(f"Table '{table}' may not exist or is inaccessible: {str(e)}")
    
    # Verify pgvector extension (requires direct SQL, suggest manual check)
    logger.info("Please ensure 'pgvector' extension is enabled via Supabase SQL Editor with: CREATE EXTENSION IF NOT EXISTS vector;")
    
    logger.info("Supabase client verification completed. Schema setup should be done via SQL Editor.")

if __name__ == "__main__":
    try:
        setup_supabase()
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}", exc_info=True)