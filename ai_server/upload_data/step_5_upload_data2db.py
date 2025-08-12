from ai_server.config_db import config_db
from ai_server.upload_data.step_4_node_metadata import get_node_metadata
from llama_index.core import StorageContext, VectorStoreIndex
from dotenv import load_dotenv
load_dotenv()
import os
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
import uuid
from llama_index.core import Document
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_API_KEY")
embedding = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)


def create_docStore(category, product_line, product_name, description, features_benefits, brochure_file_path, file_brochure_name):
    product_id = uuid.uuid1()
    metadata = {
        "category": category,
        "product_line": product_line,
        "product_name": product_name,
        "summary": description + features_benefits,
        "product_id": str(product_id),
        "type":"summary_document",
        "brochure_file_path": brochure_file_path,
        "file_brochure_name": file_brochure_name
    }
    return Document(
        text=description + features_benefits,
        metadata=metadata
    ), product_id
def upload_data2db_from_folder(folder_path, collection_name, category, product_line, product_name, description, features_benefits, brochure_file_path, file_brochure_name):
    documentStore, product_id = create_docStore(category, product_line, product_name, description, features_benefits, brochure_file_path, file_brochure_name)
    upload_docStore2db(collection_name, documentStore)
    for root, dirs, files in os.walk(folder_path):  # Duyệt tất cả thư mục con
        for file in files:
            if file.endswith(".pdf"):
                full_path = os.path.join(root, file)
                print("Uploading:", full_path)
                upload_data2db(pdf_path=full_path, collection_name=collection_name, product_id=product_id)

def upload_data2db(pdf_path, collection_name, product_id):
    vector_store = config_db(collection_name)
    documents = get_node_metadata(pdf_path, product_id)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )
    print("Upload data to database successfully")

def upload_docStore2db(collection_name, documentStore):
    vector_store = config_db(collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        [documentStore],
        storage_context=storage_context,
    )
    print("Upload docStore to database successfully")

