from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)
with driver.session() as session:
    result = session.run("RETURN 'connected from Python' AS status")
    print(result.single()["status"])
driver.close()