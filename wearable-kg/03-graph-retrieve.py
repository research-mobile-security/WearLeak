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


warnings.filterwarnings("ignore", category=ResourceWarning)
from neo4j._sync.driver import Driver

# Override the __del__ method to avoid the error
def safe_del(self):
    try:
        self.close()
    except Exception:
        pass

Driver.__del__ = safe_del

logging.getLogger('neo4j').setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=ResourceWarning)

load_dotenv()

NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_DATABASE = "kgwearable00"
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
    enhanced_schema=True
)

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125")

class Entities(BaseModel):
    names: List[str] = Field(
        ...,
        description="All the app-related entities appearing in the text",
    )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting app-related entities such as app, apptype, apikey, services, datacollected, and datashared from the text.",
        ),
        (
            "human",
            "Extract entities from the following input: {question}",
        ),
    ]
)

entity_chain = prompt | llm.with_structured_output(Entities)

def generate_full_text_query(input: str) -> str:
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

def create_fulltext_index():
    try:
        graph.query("""
        CREATE FULLTEXT INDEX entityIndex IF NOT EXISTS 
        FOR (e:App|Apptype|Apikey|Services|Datacollected|Datashared) ON EACH [e.id]
        """)
        print("Fulltext index 'entityIndex' created successfully.")
    except ClientError as e:
        if "ProcedureNotFound" in str(e):
            print("Fulltext indexing is not supported in your Neo4j version.")
        else:
            raise e

def structured_retriever(question: str) -> str:
    result = ""
    entities = entity_chain.invoke({"question": question})
    print(f"Extracted entities: {entities.names}")  # Debug entities
    # Ánh xạ entity sang giá trị thực tế
    entity_mapping = {
        "app": "Xyz.Klinker.Messenger",
        "apptype": "Standalone",
        "apikey": "Com.Google.Android.Geo.Api_Key",
        "services": "Google",
        "datacollected": "Audio",
        "datashared": "No information",  # Giá trị nếu không có
    }
    for entity in entities.names:
        mapped_value = entity_mapping.get(entity, entity)
        query = generate_full_text_query(mapped_value)
        print(f"Generated full text query: {query}")  # Debug query
        response = graph.query(
            """CALL db.index.fulltext.queryNodes('entityIndex', $query, {limit:2})
            YIELD node, score
            CALL {
              WITH node
              MATCH (node)-[r]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' + node.id AS output
            }
            RETURN output LIMIT 50
            """,
            {"query": query},
        )
        print(f"Query response: {response}")  # Debug response
        result += "\n".join([el['output'] for el in response])
    return result



# Tạo chỉ mục trước khi truy vấn
create_fulltext_index()

print("--------------------------structured_retriever--------------------------")
print(structured_retriever("What data does Xyz.Klinker.Messenger collect?"))
