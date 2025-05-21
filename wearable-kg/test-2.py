import csv
import os
import time 
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


# Neo4j Connection and Database Setup
def connect_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))

def create_database_if_not_exists(driver, database_name):
    with driver.session(database="system") as session:
        db_exists = session.execute_read(check_database_exists_tx, database_name)
        if not db_exists:
            session.execute_write(create_database_tx, database_name)
            print(f"Database '{database_name}' created successfully!")
            time.sleep(5)  # Wait for the database to initialize
        else:
            print(f"Database '{database_name}' already exists.")

def check_database_exists_tx(tx, database_name):
    result = tx.run("SHOW DATABASES")
    databases = [record["name"] for record in result]
    return database_name in databases

def create_database_tx(tx, database_name):
    tx.run(f"CREATE DATABASE {database_name}")

# Utility to Execute Cypher Queries
def execute_query(driver, cypher_query, parameters=None, database="kgwearable"):
    try:
        with driver.session(database=database) as session:
            session.run(cypher_query, parameters)
    except Exception as e:
        print(f"Error executing query: {e}")

# Dynamic Node and Relationship Creation
def create_knowledge_graph(driver, json_data):
    root_id = json_data["_id"]
    
    # Root Node
    execute_query(driver, "MERGE (root:App {id: $id})", {"id": root_id})

    # Key-to-relationship mapping
    key_relationship_map = {
        "manifest_permission": "has_permission",
        "tag-action": "has_action",
        "tag-application": "has_application",
        "tag-data": "has_data",
        "tag-provider": "has_provider",
        "tag-receiver": "has_receiver",
        "tag-service": "has_service",
        "tag-uses-feature": "has_feature",
        "tag-uses-library": "has_library",
        "data-shared": "share_data",
        "data-collected": "collect_data",
    }

    for key, relationship in key_relationship_map.items():
        value = json_data.get(key)

        if value:
            if isinstance(value, list):
                for item in value:
                    node_text = item if not isinstance(item, dict) else ", ".join([f"{k}: {v}" for k, v in item.items()])
                    cypher_query = f"""
                        MERGE (node:Node {{text: $text}})
                        MERGE (root:App {{id: $root_id}})
                        MERGE (root)-[:{relationship.upper()}]->(node)
                    """
                    execute_query(driver, cypher_query, {"text": node_text, "root_id": root_id})
            else:
                node_text = value if not isinstance(value, dict) else ", ".join([f"{k}: {v}" for k, v in value.items()])
                cypher_query = f"""
                    MERGE (node:Node {{text: $text}})
                    MERGE (root:App {{id: $root_id}})
                    MERGE (root)-[:{relationship.upper()}]->(node)
                """
                execute_query(driver, cypher_query, {"text": node_text, "root_id": root_id})

# Main Script Execution
if __name__ == "__main__":
    # Connection Details
    NEO4J_URI = os.environ["NEO4J_URI"]
    NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
    NEO4J_DATABASE = "kgwearable"
    NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

    # Connect to Neo4j
    driver = connect_neo4j(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Ensure Database Exists
    create_database_if_not_exists(driver, NEO4J_DATABASE)

    # JSON Data
    json_data = {
        '_id': 'xyz.klinker.messenger',
        'manifest_permission': [
            'android.permission.SEND_SMS', 'android.permission.READ_SMS', 'android.permission.WRITE_SMS', 'android.permission.RECEIVE_SMS'
        ],
        'tag-action': [
            {'name': 'android.intent.action.SENDTO'},
            {'name': 'com.appsflyer.referrer.INSTALL_PROVIDER'}
        ],
        'tag-application': [
            {'theme': '@7F1501DF', 'label': '@7F1400B2', 'icon': '@7F110002', 'name': 'xyz.klinker.messenger.MessengerApplication'}
        ],
        'tag-data': [
            {'scheme': 'smsto', 'host': '*'},
            {'scheme': 'https'}
        ],
        'tag-provider': [
            {'name': 'androidx.core.content.FileProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.provider'}
        ],
        'tag-receiver': [
            {'name': 'xyz.klinker.messenger.shared.widget.MessengerAppWidgetProvider', 'exported': 'true'}
        ],
        'tag-service': 'not-found',
        'tag-uses-feature': [
            {'name': 'android.hardware.camera', 'required': 'false'}
        ],
        'tag-uses-library': [
            {'name': 'com.sec.android.app.multiwindow', 'required': 'false'}
        ],
        'data-shared': 'No information',
        'data-collected': ['Audio', 'Personal info', 'Photos and videos']
    }

    # Create the Knowledge Graph
    create_knowledge_graph(driver, json_data)

    # Close the Driver
    driver.close()
