from neo4j import GraphDatabase
import logging
import os
from dotenv import load_dotenv
load_dotenv()
# Function to create a knowledge graph from the JSON data
def create_knowledge_graph(json_data, neo4j_uri, neo4j_username, neo4j_password):
    # Connect to Neo4j
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    def create_nodes_and_relationships(tx, data):
        try:
            # Create the root node
            root_id = data["_id"]
            print(f"Creating root node with id: {root_id}")
            tx.run("MERGE (app:App {id: $id})", id=root_id)

            # Define keys and relationships
            keys_relationships = {
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

            # Loop through each key and create nodes and relationships
            for key, relationship in keys_relationships.items():
                value = data.get(key)
                if value:
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                text = ", ".join([f"{k}: {v}" for k, v in item.items()])
                            else:
                                text = str(item)
                            print(f"Creating node for key: {key}, value: {text}")
                            tx.run(
                                """
                                MERGE (node:Node {text: $text})
                                MERGE (app:App {id: $id})
                                MERGE (app)-[:RELATES_TO {type: $relationship}]->(node)
                                """,
                                id=root_id,
                                text=text,
                                relationship=relationship,
                            )
                    else:
                        text = str(value)
                        print(f"Creating single node for key: {key}, value: {text}")
                        tx.run(
                            """
                            MERGE (node:Node {text: $text})
                            MERGE (app:App {id: $id})
                            MERGE (app)-[:RELATES_TO {type: $relationship}]->(node)
                            """,
                            id=root_id,
                            text=text,
                            relationship=relationship,
                        )
        except Exception as e:
            print(f"Error while creating nodes and relationships: {e}")

    # Execute the transaction
    try:
        with driver.session() as session:
            print("Starting transaction to create nodes and relationships.")
            session.execute_write(create_nodes_and_relationships, json_data)
            print("Transaction completed.")
    except Exception as e:
        print(f"Error in Neo4j session: {e}")
    finally:
        driver.close()
        print("Neo4j driver closed.")

# JSON data as Python dict
json_data = {
    '_id': 'xyz.klinker.messenger',
    'manifest_permission': [
        'android.permission.SEND_SMS', 'android.permission.READ_SMS', 'android.permission.WRITE_SMS', 'android.permission.RECEIVE_SMS'
    ],
    'tag-action': [
        {'name': 'android.intent.action.SENDTO'}, {'name': 'com.appsflyer.referrer.INSTALL_PROVIDER'},
        {'name': 'androidx.browser.customtabs.CustomTabsService'}, {'name': 'android.intent.action.VIEW'}
    ],
    'tag-application': [
        {
            'theme': '@7F1501DF', 'label': '@7F1400B2', 'icon': '@7F110002',
            'name': 'xyz.klinker.messenger.MessengerApplication', 'allowBackup': 'false', 'hardwareAccelerated': 'true',
            'largeHeap': 'true', 'supportsRtl': 'true', 'banner': '@7F110001', 'extractNativeLibs': 'false',
            'fullBackupContent': '@7F180003', 'networkSecurityConfig': '@7F180012', 'appCategory': '4',
            'appComponentFactory': 'androidx.core.app.CoreComponentFactory'
        }
    ],
    'tag-data': [
        {'scheme': 'smsto', 'host': '*'}, {'scheme': 'https'}, {'scheme': 'http'}, {'scheme': 'market'}
    ],
    'tag-provider': [
        {'name': 'androidx.core.content.FileProvider', 'exported': 'false', 'authorities': 'xyz.klinker.messenger.provider', 'grantUriPermissions': 'true'}
    ],
    'tag-receiver': [
        {'name': 'xyz.klinker.messenger.shared.widget.MessengerAppWidgetProvider', 'exported': 'true'}
    ],
    'tag-service': 'not-found',
    'tag-uses-feature': [
        {'name': 'android.hardware.camera', 'required': 'false'}, {'name': 'android.hardware.microphone', 'required': 'false'}
    ],
    'tag-uses-library': [
        {'name': 'com.sec.android.app.multiwindow', 'required': 'false'}, {'name': 'org.apache.http.legacy', 'required': 'false'}
    ],
    'data-shared': 'No information',
    'data-collected': [
        'Audio', 'Personal info', 'Photos and videos'
    ]
}

# Neo4j connection details
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_DATABASE = "kgwearable"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

# Create the knowledge graph
create_knowledge_graph(json_data, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
