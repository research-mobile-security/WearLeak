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
### LLMs - Langchain
import openai
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
### Summary chain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, MapReduceChain, load_summarize_chain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_community.document_loaders import TextLoader
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
def write_string_to_txt(content, file_path):
    try:
        # Check if the file exists and remove it
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Write the new content to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"Content successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")


def extract_output_text_as_dict(response):
    """
    Extracts the 'output_text' from the response, cleans it, and converts it into a dictionary.

    :param response: The response dictionary containing 'output_text'.
    :return: A dictionary parsed from the 'output_text', or None if parsing fails.
    """
    # Get the output_text from the response
    output_text = response.get("output_text", "")
    
    # Remove code block markers (```json and ```) if present
    if output_text.startswith("```json"):
        output_text = output_text[len("```json"):].strip("`").strip()
    
    try:
        # Convert the cleaned JSON string into a dictionary
        output_dict = json.loads(output_text)
        return output_dict
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
#################-------------- Database connection --------------#################
mongoDB_uri = 'mongodb://localhost:27017'
mongoDB_database = 'wearable-project' 
# mongoDB_collection = 'wearable-app'
# standalone
mongoDB_collection = 'wearable-standalone'
json_directory_path = "./json-tmp/"
llm_response_path = "./llm-response/"
#################-------------- MAIN --------------#################
# 1. Connect to the MongoDB collection
collection = connect_mongodb(mongoDB_uri,mongoDB_database,mongoDB_collection)
element_id = "xyz.klinker.messenger"  # app.groupcal.www xyz.klinker.messenger
data = get_data_by_id(collection, element_id)
# print(data)
# 2. Remove unwanted data
keys_to_remove = ['apkfile_name', 'apkfile_name_new', 'extract_manifest', 'app_group', 'app_group_reason', 'ggplaystore']
json_data = remove_keys_from_json(data, keys_to_remove)
# print(json_data)
# print_dict_as_json(json_data)
# 3. Get app manifest element
app_id = json_data["_id"]
app_permission = json_data["manifest_permission"]
app_action = json_data["tag-action"]
app_application = json_data["tag-application"]
app_data = json_data["tag-data"]
app_property = json_data["tag-property"]
app_provider = json_data["tag-provider"]
app_receiver = json_data["tag-receiver"]
app_service = json_data["tag-service"]
app_uses_feature = json_data["tag-uses-feature"]
app_uses_library = json_data["tag-uses-library"]
app_meta_data = json_data["tag-meta-data"]
# 4. Chat model
# Setup model
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key
llm = ChatOpenAI(model="gpt-4o",temperature=0)

# template = """You are an expert in Android OS and Wear OS.

# Based on the manifest information of the Android app with package name {app_id} with information including manifest permission is {app_permission}, \n 
# tag-action is {app_action}, \n 
# tag-application is {app_application}, \n
# tag-data is {app_data}, \n
# tag-property is {app_property}, \n
# tag-provider is {app_provider}, \n
# tag-receiver is {app_receiver}, \n
# tag-service is {app_service}, \n
# tag-uses-feature is {app_uses_feature}, \n
# tag-uses-library is {app_uses_library} and \n
# tag-meta-data is {app_meta_data}. \n

# Determine the type of the app is companion app, embedded app or standalone app. In addition, determine whether the app integrates Google Fit or not?

# Provide a concise explanation for your reasoning.
# """
template = """You are an expert in Android OS and Wear OS.

Based on the manifest information of the Android app with package name {app_id} with information including manifest permission is {app_permission}, \n 
tag-action is {app_action}, \n 
tag-application is {app_application}, \n
tag-data is {app_data}, \n
tag-property is {app_property}, \n
tag-provider is {app_provider}, \n
tag-receiver is {app_receiver}, \n
tag-service is {app_service}, \n
tag-uses-feature is {app_uses_feature}, \n
tag-uses-library is {app_uses_library} and \n
tag-meta-data is {app_meta_data}. \n

Determine the type of the app is companion app, embedded app or standalone app. 
In addition, determine whether the app integrates any 3rd service (google, facebook, advertising, etc.)
For 3rd service integration specify the API/SDK that the app uses, for example `com.google.android.c2dm.permission.RECEIVE` for Firebase Cloud Messaging.
Provide a concise explanation for your reasoning.
"""
# Respond *only* with a JSON object in the example following format:
# {{"_id": "app_id", "app_type": "companion/standalone/embedded","google_fit":"no/yes"}}
prompt = PromptTemplate(
    input_variables=[
        "app_id",
        "app_permission",
        "app_action",
        "app_application",
        "app_data",
        "app_property",
        "app_provider",
        "app_receiver",
        "app_service",
        "app_uses_feature",
        "app_uses_library",
        "app_meta_data"
    ],
    template=template,
)
example_input = {
    "app_id": app_id,
    "app_permission": app_permission,
    "app_action": app_action,
    "app_application": app_application,
    "app_data": app_data,
    "app_property": app_property,
    "app_provider": app_provider,
    "app_receiver": app_receiver,
    "app_service": app_service,
    "app_uses_feature": app_uses_feature,
    "app_uses_library": app_uses_library,
    "app_meta_data": app_meta_data
}

formatted_prompt = prompt.format(**example_input)
print("formatted_prompt:", formatted_prompt)
response = llm.invoke(formatted_prompt)
print("------------- LLM response -------------")
print(response.content)
llm_response_file = llm_response_path+app_id+".txt"
write_string_to_txt(response.content, llm_response_file)
# 5. Summary chain
print("------------- Summary Chain -------------")
# prompt_template = """
# You are provided with a paragraph about the app's classification (e.g. companion app, embedded app, or standalone app) and the 3rd party services the app integrates with (e.g. Google, Facebook, advertising, etc.)
# ----------
# {text}
# ----------
# Question: Respond *only* with a JSON object in the example following format:
# {{"_id": "package name", "app_type": "companion/standalone/embedded","3rd_integration":{{"service name": "import library or SDK or API"}}}}
# """
# prompt_template = """
# You are provided with a paragraph about the app's classification (e.g. companion app, embedded app, or standalone app) and the 3rd party services the app integrates with (e.g. Google, Facebook, advertising, etc.)
# ----------
# {text}
# ----------
# Question: Based on the provided paragraph, respond *only* with a JSON object in the following format:
# {{
#     "_id": "package name",
#     "app_type": "companion/standalone/embedded",
#     "3rd_integration": {{
#         "service name": "import library or SDK or API"
#     }}
# }}

# Make sure:
# 1. The `"_id"` field contains the app's package name.
# 2. The `"app_type"` field accurately reflects whether the app is a companion app, standalone app, or embedded app.
# 3. The `"3rd_integration"` field includes key-value pairs where the keys are the names of the third-party services integrated with the app (e.g., Google, Facebook, CleverTap, Zendesk), and the values are the respective libraries, SDKs, or APIs used for the integration. For example, `com.google.android.c2dm.permission.RECEIVE` for Firebase Cloud Messaging, the value is com.google.android.c2dm.permission.RECEIVE
# 4. Respond only with a valid JSON object, and avoid any additional explanations.
# """
prompt_template = """
You are provided with a paragraph about the app's classification (e.g. companion app, embedded app, or standalone app) and the 3rd party services the app integrates with (e.g. Google, Facebook, advertising, etc.)
----------
{text}
----------
Question: Based on the provided paragraph, respond *only* with a JSON object in the following format:
{{
    "_id": "package name",
    "app_type": "companion/standalone/embedded",
    "3rd_integration": {{
        "service name": "list of permissions, metadata, or APIs"
    }}
}}

Make sure:
1. The `"_id"` field contains the app's package name.
2. The `"app_type"` field accurately reflects whether the app is a companion app, standalone app, or embedded app.
3. The `"3rd_integration"` field includes key-value pairs where:
   - The keys are the names of third-party services integrated with the app (e.g., Google, Facebook, CleverTap, Zendesk).
   - The values are a comma-separated list of permissions, metadata, or APIs that indicate the use of these services. 
   For example:
      - `com.google.android.c2dm.permission.RECEIVE` indicates the use of Firebase Cloud Messaging for push notifications.
      - `com.google.firebase.provider.FirebaseInitProvider` and related metadata suggest the use of Firebase services, including Firebase Analytics, Firebase Crashlytics, and Firebase Auth.
      - `com.google.android.gms.wearable.DATA_CHANGED` suggests integration with Google Wearable services.
      - `com.google.android.gms.auth.api.phone.SMS_RETRIEVED` indicates the use of Google's SMS Retriever API.
4. Respond only with a valid JSON object, and avoid any additional explanations.
"""

prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# Load the summarize chain
stuff_chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt, verbose=True)

# Load documents from the file
loader = TextLoader(llm_response_file)
code_purpose_docs = loader.load()

# Ensure the documents are in list format
if not isinstance(code_purpose_docs, list):
    code_purpose_docs = [code_purpose_docs]

# Convert documents into the format expected by the chain
output_summary = stuff_chain.invoke({"input_documents": code_purpose_docs})

# Print the summary

output_summary_dict = extract_output_text_as_dict(output_summary)
print(output_summary_dict)
