import csv
import os
import time 
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
load_dotenv()
from pymongo import MongoClient
from bson.objectid import ObjectId
from langchain_community.graphs import Neo4jGraph
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
        "api_key": "configured",
        "third_party_service": "integrated",
        "app_type": "has_type",
        "data_shared": "share_data",
        "data_collected": "collect_data",
    }

    for key, relationship in key_relationship_map.items():
            cypher_query = f"""
                MERGE (node:{key.replace('-', '_').title()} {{name: $key}})
                MERGE (root:App {{id: $root_id}})
                MERGE (root)-[:{relationship.upper()}]->(node)
            """
            execute_query(driver, cypher_query, {"key": key, "root_id": root_id})
def insert_data_to_node(driver, node_name, data, database_name):
    """
    Add data directly to the specified node in Neo4j.
    
    Args:
        driver: The Neo4j driver instance.
        node_name: The name of the node (e.g., 'manifest_permission').
        data: The data to add (list, dictionary, or string).
    """
    # Convert nested dictionaries or lists to JSON strings for storage
    if isinstance(data, (dict, list)):
        data = json.dumps(data)  # Convert to JSON string

    cypher_query = f"""
    MATCH (node:{node_name.replace('-', '_').title()} {{name: $node_name}})
    SET node.data = $data
    """
    try:
        with driver.session(database=database_name) as session:
            session.run(cypher_query, {"node_name": node_name, "data": data})
        print(f"Data added to '{node_name}' node successfully!")
    except Exception as e:
        print(f"Error adding data to '{node_name}' node: {e}")
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
def remove_keys_from_json(json_data, keys_to_remove):
    for key in keys_to_remove:
        if key in json_data:
            del json_data[key]
    return json_data
def list_to_sequential_dict(lst, key_prefix='permission'):
    """
    Converts a list into a dictionary with sequential keys.
    
    Parameters:
    - lst (list): The list to convert.
    - key_prefix (str): Prefix for the keys in the dictionary.
    
    Returns:
    - dict: A dictionary with sequentially named keys and the list items as values.
    """
    return {f"{key_prefix}-{i}": item for i, item in enumerate(lst)}
# Main Script Execution
if __name__ == "__main__":
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
    element_id = "xyz.klinker.messenger"  #
    data = get_data_by_id(collection, element_id)
    # print(data)
    # 2. Remove unwanted data
    keys_to_remove = ['apkfile_name', 'apkfile_name_new', 'extract_manifest', 
                      'app_group', 'app_group_reason', 'ggplaystore',
                      'tag-action', 'tag-application', 'tag-data',
                      'tag-property', 'tag-provider', 'tag-receiver',
                      'tag-service', 'tag-uses-feature', 'tag-uses-library',
                      'tag-meta-data'
                      ]
    json_data_graph = remove_keys_from_json(data, keys_to_remove)
    print(json_data_graph)
    package_name = json_data_graph["_id"]
    # manifest_permission_array = json_data_graph["manifest_permission"]
    # manifest_permission = list_to_sequential_dict(manifest_permission_array)
    app_type = json_data_graph["app_type"]
    api_key = json_data_graph["api_key"]
    third_party_service = json_data_graph["3rd_integration"]
    data_shared = json_data_graph["data-shared"]
    data_collected = json_data_graph["data-collected"]
    print("package_name",package_name)
    # print("manifest_permission",manifest_permission)
    print("app_type",app_type)
    print("api_key",api_key)
    print("third_party_service",third_party_service)
    print("data_shared",data_shared)
    print("data_collected",data_collected)
    # NEO4J GRAPH
    # NEO4J local
    NEO4J_URI = os.environ["NEO4J_URI"]
    NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
    NEO4J_DATABASE = "kgwearable00"
    NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
    AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)
    
    # NEO4J cloud
    # NEO4J_URI = os.environ["NEO4J_URI_CLOUD"]
    # NEO4J_USERNAME = os.environ["NEO4J_USERNAME_CLOUD"]
    # NEO4J_DATABASE = os.environ["NEO4J_USERNAME_CLOUD"]
    # NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD_CLOUD"]
    # AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Connect to Neo4j
    driver = connect_neo4j(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Ensure Database Exists
    create_database_if_not_exists(driver, NEO4J_DATABASE)
    # Create graph
    from langchain_experimental.graph_transformers import LLMGraphTransformer
    from langchain_openai import ChatOpenAI
    from langchain_core.documents import Document

    # Setup LLM
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo")
    # text = f"""
    #     The app with package name {package_name} is classified (app_type) as {app_type}, requires manifest_permission as {manifest_permission} and has configured api_key (if any) as {api_key}. This app integrates with 3rd service (third_party_service) including {third_party_service}. Finally, the app collects data (data_collected) as {data_collected} and shares data (data_shared) as {data_shared}.
    # """
    text = f"""
        The app with package name {package_name} is classified (app_type) as {app_type} and has configured api_key (if any) as {api_key}. 
        This app integrates with 3rd service (third_party_service) including {third_party_service}. 
        Finally, the app collects data (data_collected) as {data_collected} and shares data (data_shared) as {data_shared}.
    """
    document = Document(page_content=text)

    # Setup graph transformer
    llm_transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["App","AppType", "APIKey", "Services", "DataCollected", "DataShared"],
        allowed_relationships=["CLASSIFIED_AS", "USES_API_KEY", "INTEGRATES_WITH", "COLLECTS", "SHARES"]
    )

    # Convert document to graph
    graph_documents = llm_transformer.convert_to_graph_documents([document])

    # Print nodes and relationships
    # for graph in graph_documents:
    #     print(f"Nodes: {graph.nodes}")
    #     print(f"Relationships: {graph.relationships}")
    graph = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
        enhanced_schema=True
    )
    graph.add_graph_documents(graph_documents)



