# Load data
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import time
import json
from langchain_community.document_loaders import JSONLoader
# Knowledge graph
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Tuple, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_community.document_loaders import WikipediaLoader
from langchain.text_splitter import TokenTextSplitter
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.runnables import ConfigurableField, RunnableParallel, RunnablePassthrough
import logging
import time
from langchain_core.documents import Document
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
json_file_path = json_directory_path+element_id+".json"
write_dict_to_json_file(data, json_file_path)
# 2. Load data as type <class 'langchain_core.documents.base.Document'>
json_document = load_json_data(json_file_path,"")
# print(json_document)
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

### 3.5. Initialize the Neo4j graph
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
    enhanced_schema=True
)
### 3.6. Construct a graph
llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125") # gpt-4-0125-preview occasionally has issues
llm_transformer = LLMGraphTransformer(llm=llm)

graph_documents = llm_transformer.convert_to_graph_documents(data)
graph.add_graph_documents(
    graph_documents,
    baseEntityLabel=True,
    include_source=True
)
print("Documents added to graph!")
