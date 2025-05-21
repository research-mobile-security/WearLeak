from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
import warnings
import logging
from neo4j.exceptions import ClientError

# Suppress warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
from neo4j._sync.driver import Driver

# Override the __del__ method to avoid the error
def safe_del(self):
    try:
        self.close()
    except Exception:
        pass

Driver.__del__ = safe_del

# Logging setup
logging.getLogger("neo4j").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=ResourceWarning)

# Load environment variables
load_dotenv()

NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_DATABASE = "kgwearable00"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

# Initialize the graph
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
    enhanced_schema=True,
)

# Setup LLM
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125")

# Define the entity extraction class
class Entities(BaseModel):
    names: List[str] = Field(
        ...,
        description="All the app-related entities appearing in the text",
    )

# Define the entity extraction prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting app-related entities and relationships such as 'collect', 'share', 'use API key', 'integrate with', etc., from the text.",
        ),
        (
            "human",
            "Extract the relationship type and entities from the following input: {question}",
        ),
    ]
)

entity_chain = prompt | llm.with_structured_output(Entities)

# Function to generate a full-text query
def generate_full_text_query(input: str) -> str:
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

# Create the full-text index
def create_fulltext_index():
    try:
        graph.query(
            """
            CREATE FULLTEXT INDEX entityIndex IF NOT EXISTS 
            FOR (e:App|AppType|APIKey|Services|DataCollected|DataShared) ON EACH [e.id]
            """
        )
        print("Fulltext index 'entityIndex' created successfully.")
    except ClientError as e:
        if "ProcedureNotFound" in str(e):
            print("Fulltext indexing is not supported in your Neo4j version.")
        else:
            raise e

# Structured retriever to get filtered relationships
def structured_retriever(question: str) -> str:
    result = ""
    # Extract entities and relationships from the question
    entities = entity_chain.invoke({"question": question})
    print(f"Extracted entities: {entities.names}")  # Debug: Display extracted entities

    # Determine the relationship type based on the question
    relationship_type = None
    if "collect" in question.lower():
        relationship_type = "COLLECTS"
    elif "share" in question.lower():
        relationship_type = "SHARES"
    elif "api key" in question.lower():
        relationship_type = "USES_API_KEY"
    elif "integrate" in question.lower():
        relationship_type = "INTEGRATES_WITH"
    elif "classify" in question.lower():
        relationship_type = "CLASSIFIED_AS"

    if relationship_type is None:
        return "Could not determine the relationship type from the question."

    for entity in entities.names:
        query = generate_full_text_query(entity)
        print(f"Generated full text query: {query}")  # Debug: Display generated query
        response = graph.query(
            f"""
            CALL db.index.fulltext.queryNodes('entityIndex', $query, {{limit:2}})
            YIELD node, score
            CALL {{
              WITH node
              MATCH (node)-[r:{relationship_type}]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
            }}
            RETURN output LIMIT 50
            """,
            {"query": query},
        )
        print(f"Query response: {response}")  # Debug: Display query response
        result += "\n".join([el["output"] for el in response])
    return result

# Create the index before querying
create_fulltext_index()

# Perform the query
print("--------------------------structured_retriever--------------------------")
# print(structured_retriever("What data does Xyz.Klinker.Messenger collect?"))
# print(structured_retriever("What data does Xyz.Klinker.Messenger share?"))
# print(structured_retriever("What API key does Xyz.Klinker.Messenger use?"))
# print(structured_retriever("What services does Xyz.Klinker.Messenger integrate with?"))
print(structured_retriever("What is does Xyz.Klinker.Messenger?"))