import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("update_neo4j.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Neo4jUpdate:
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

    def update_schema(self):
        try:
            with self.driver.session() as session:
                # Create constraints
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Campaign) REQUIRE c.campaign_id IS UNIQUE")
                logger.info("Neo4j campaign constraint created")

                # Add sample data (admin, volunteer, campaign, location)
                session.run("""
                    MERGE (u1:User {user_id: $admin_id, email: $admin_email, location: $admin_location})
                    MERGE (u2:User {user_id: $volunteer_id, email: $volunteer_email, location: $volunteer_location})
                    MERGE (c:Campaign {campaign_id: $campaign_id, name: $campaign_name})
                    MERGE (u1)-[:PARTICIPATES_IN]->(c)
                    MERGE (u2)-[:PARTICIPATES_IN]->(c)
                    MERGE (u1)-[:LOCATED_IN]->(:Location {name: $admin_location})
                    MERGE (u2)-[:LOCATED_IN]->(:Location {name: $volunteer_location})
                    MERGE (c)-[:CONTAINS_DOCUMENT]->(d:Document {document_id: $document_id, file_name: $file_name})
                """, 
                    admin_id="6c16ffdf-f6dd-4e9f-baaa-92a02f7a7dfb",  # Replace with real admin user_id
                    admin_email="admin@example.com",
                    admin_location="New York",
                    volunteer_id="volunteer-uuid-123",  # Replace with real volunteer user_id
                    volunteer_email="volunteer_test_8478b3ba@mailinator.com",
                    volunteer_location="Boston",
                    campaign_id="campaign-uuid-001",
                    campaign_name="Platinum Plan Campaign",
                    document_id="test-document-uuid",
                    file_name="president-trump-platinum-plan-final-version.pdf")
                logger.info("Neo4j schema updated with sample data")
        except Exception as e:
            logger.error(f"Failed to update Neo4j schema: {str(e)}", exc_info=True)
            raise

def update_neo4j():
    try:
        neo4j_update = Neo4jUpdate()
        neo4j_update.update_schema()
        neo4j_update.close()
    except Exception as e:
        logger.error(f"Neo4j update failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    update_neo4j()