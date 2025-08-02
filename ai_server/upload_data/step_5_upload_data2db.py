from config_db import config_db
from step_4_node_metadata import get_node_metadata
from llama_index.core import StorageContext, VectorStoreIndex
from dotenv import load_dotenv
load_dotenv()
import os
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
embedding = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)

def upload_data2db_from_folder(folder_path, collection_name):
    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            upload_data2db(os.path.join(folder_path, file), collection_name)

def upload_data2db(pdf_path, collection_name):
    vector_store = config_db(collection_name)
    documents = get_node_metadata(pdf_path)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )
    print("Upload data to database successfully")


upload_data2db(pdf_path="/Users/nguyensiry/Downloads/filling_slot/documents/Controller_Brochure.pdf", collection_name="Electech")