import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("setup_neo4j.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Neo4jSetup:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        if not all([self.uri, self.user, self.password]):
            logger.error(f"Neo4j configuration missing: URI={self.uri}, User={self.user}, Password={'set' if self.password else 'not set'}")
            raise ValueError("Neo4j configuration missing")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        logger.info("Neo4j driver initialized")

    def close(self):
        self.driver.close()
        logger.info("Neo4j driver closed")

    def setup_schema(self):
        try:
            with self.driver.session() as session:
                # Create constraints
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE")
                logger.info("Neo4j constraints created")

                # Create sample data (example user and document)
                session.run("""
                    MERGE (u:User {user_id: $user_id, email: $email})
                    MERGE (d:Document {document_id: $document_id, file_name: $file_name})
                    MERGE (u)-[:CONTAINS_DOCUMENT]->(d)
                """, user_id="6c16ffdf-f6dd-4e9f-baaa-92a02f7a7dfb",  # Replace with real admin user_id
                    email="admin@example.com",
                    document_id="test-document-uuid",
                    file_name="president-trump-platinum-plan-final-version.pdf")
                logger.info("Sample Neo4j data created")
        except Exception as e:
            logger.error(f"Failed to setup Neo4j schema: {str(e)}", exc_info=True)
            raise

def setup_neo4j():
    try:
        neo4j_setup = Neo4jSetup()
        neo4j_setup.setup_schema()
        neo4j_setup.close()
    except Exception as e:
        logger.error(f"Neo4j setup failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    setup_neo4j()