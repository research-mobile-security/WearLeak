# Load data
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import time
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging
import time
import neo4j
import warnings
from neo4j._sync.driver import Driver
#################-------------- Function --------------#################
def connect_mongodb(uri,db_name, collection_name):
    # Connect to MongoDB 
    client = MongoClient(uri)
    
    # Select the database and collection
    db = client[db_name]
    collection = db[collection_name]
    
    return collection

def get_data_by_id(collection, id_value):
    try:
        # Try to cast id_value to ObjectId if it is a valid ObjectId
        try:
            id_value = ObjectId(id_value)
        except:
            # If it is not a valid ObjectId, leave it as is (e.g., string _id)
            pass
        
        document = collection.find_one({"_id": id_value})
        return document
    except Exception as e:
        print(f"Error: {e}")
        return None

def write_dict_to_json_file(data, file_path):
    try:
        # Check if the file exists and remove it
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Old file {file_path} removed.")
        
        # Write the new data to the file
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        print(f"Data successfully written to {file_path}")
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False
def load_json_data(file_path,jq_schema):
    # Define the JSONLoader with the appropriate parameters
    loader = JSONLoader(
        file_path=file_path,
        jq_schema='.'+jq_schema,
        text_content=False
    )
    # Load the JSON data
    data = loader.load()
    return data
def print_data_clearly(data):
    for item in data:
        # Access metadata and page_content from the Document object
        print("Metadata:")
        print(json.dumps(item.metadata, indent=4))  # Use dot notation to access metadata
        
        print("\nPage Content:")
        try:
            # Parse and pretty-print the JSON content from page_content
            page_content = json.loads(item.page_content)
            print(json.dumps(page_content, indent=4))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in page_content: {e}")
        print("-" * 80)
# Function to create the database if it does not exist
def create_database_if_not_exists(driver, database_name):
    try:
        with driver.session(database="system") as session:
            db_exists = session.execute_read(check_database_exists_tx, database_name)
            if not db_exists:
                session.execute_write(create_database_tx, database_name)
                print(f"Database '{database_name}' created successfully!")
                time.sleep(5)
            else:
                print(f"Database '{database_name}' already exists.")
    except neo4j.exceptions.ClientError as e:
        if 'ExistingDatabaseFound' in str(e):
            print(f"Database '{database_name}' already exists, skipping creation.")
        else:
            raise e

# Helper functions to check if the database exists and create it
def check_database_exists_tx(tx, database_name):
    result = tx.run("SHOW DATABASES")
    databases = [record["name"] for record in result]
    return database_name in databases

def create_database_tx(tx, database_name):
    tx.run(f"CREATE DATABASE {database_name}")
    
def remove_keys_from_json(json_data, keys_to_remove):
    for key in keys_to_remove:
        if key in json_data:
            del json_data[key]
    return json_data
def print_dict_as_json(data):
    try:
        # formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
        formatted_json = json.dumps(data,ensure_ascii=False)
        print(formatted_json)
    except Exception as e:
        print(f"Error printing JSON: {e}")
# Function to create a knowledge graph from the JSON data
from neo4j import GraphDatabase
import logging

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
#################-------------- Database connection --------------#################
mongoDB_uri = 'mongodb://localhost:27017'
mongoDB_database = 'wearable-project' 
# mongoDB_collection = 'wearable-app'
# standalone
mongoDB_collection = 'wearable-standalone'
json_directory_path = "./json-tmp/"
#################-------------- MAIN --------------#################
# 1. Connect to the MongoDB collection
collection = connect_mongodb(mongoDB_uri,mongoDB_database,mongoDB_collection)
element_id = "xyz.klinker.messenger"  # thay bằng _id thực tế trong DB của bạn
data = get_data_by_id(collection, element_id)
# print(data)
# 2. Remove unwanted data
keys_to_remove = ['apkfile_name', 'apkfile_name_new', 'extract_manifest', 'app_group', 'app_group_reason', 'ggplaystore']
json_data = remove_keys_from_json(data, keys_to_remove)
print(json_data)
# print_dict_as_json(json_data)
# 3. create knowledge graph
warnings.filterwarnings("ignore", category=ResourceWarning)
# Override the __del__ method to avoid the error
# to fix this error "TypeError: catching classes that do not inherit from BaseException is not allowed"
def safe_del(self):
    try:
        self.close()
    except Exception:
        pass

Driver.__del__ = safe_del


### 3.1. Set logging level for neo4j
logging.getLogger('neo4j').setLevel(logging.ERROR)

### 3.2. Load environment variables
load_dotenv()
### 3.3. Neo4j Environment Setup
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_DATABASE = "kgwearable"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
### 3.4 Create the database if not exists
driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)
try:
    database_name = NEO4J_DATABASE
    create_database_if_not_exists(driver, database_name)
finally:
    driver.close()  # Explicitly close the driver to release resources properly


create_knowledge_graph(json_data, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)