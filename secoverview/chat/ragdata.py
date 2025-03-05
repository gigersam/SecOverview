import os
import json
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from chromadb.config import Settings
from chromadb import Client
from .models import APIData, RAGPool, UploadedFile

# Create a global Chroma client (with or without custom settings)
client = Client(Settings(anonymized_telemetry=False,))

# Maintain a dictionary of known collections & their associated retrievers
collection_dict = {}
retriever_dict = {}

# Initialize Ollama embeddings using DeepSeek-R1
embedding_function = OllamaEmbeddings(model="deepseek-r1:8b")

def init_collection(collection_name: str):
    try:
        pass
    except:
        pass

    collection = client.get_or_create_collection(name=collection_name)
    vectorstore = Chroma(
        collection_name=collection_name,
        client=client,
        embedding_function=embedding_function
    )
    retriever = vectorstore.as_retriever()
    collection_dict[collection_name] = collection
    retriever_dict[collection_name] = retriever

    return collection_dict[collection_name], retriever_dict[collection_name]

def generate_embedding(chunk):
    return embedding_function.embed_query(chunk.page_content)

def pdfloader(file_path, collection_name="foundations_of_llms"):
    collection, _ = init_collection(collection_name)
    loader = PyMuPDFLoader(file_path.file.path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    chunks = text_splitter.split_documents(documents)

    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, chunks))

    for idx, chunk in enumerate(chunks):
        doc_id = f"{collection_name}_{idx}"
        collection.add(
            documents=[chunk.page_content],
            metadatas=[{'id': doc_id}],
            embeddings=[embeddings[idx]],
            ids=[str(doc_id)]
        )

    print(f"PDF loaded into collection: {collection_name}. Added {len(chunks)} chunks.")

def txtloader(file_path, collection_name="foundations_of_llms"):
    collection, _ = init_collection(collection_name)
    with open(file_path.file.path, 'r', encoding='utf-8') as file:
        text = file.read()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    chunks = text_splitter.create_documents([text])

    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, chunks))

    for idx, chunk in enumerate(chunks):
        doc_id = f"{collection_name}_txt_{idx}"
        collection.add(
            documents=[chunk.page_content],
            metadatas=[{'id': doc_id}],
            embeddings=[embeddings[idx]],
            ids=[str(doc_id)]
        )

    print(f"TXT file loaded into collection: {collection_name}. Added {len(chunks)} chunks.")

def jsonloader(file_path, collection_name="foundations_of_llms"):
    collection, _ = init_collection(collection_name)
    with open(file_path.file.path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        text = json.dumps(data, indent=2)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    chunks = text_splitter.create_documents([text])

    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, chunks))

    for idx, chunk in enumerate(chunks):
        doc_id = f"{collection_name}_json_{idx}"
        collection.add(
            documents=[chunk.page_content],
            metadatas=[{'id': doc_id}],
            embeddings=[embeddings[idx]],
            ids=[str(doc_id)]
        )

    print(f"JSON file loaded into collection: {collection_name}. Added {len(chunks)} chunks.")

def fetch_api_data(api_url, header, params=None):
    """
    Fetch data from an API.
    
    :param api_url: The endpoint URL.
    :param params: Optional query parameters.
    :return: API response text (JSON or plain text).
    """
    try:
        if header == "" or header == None:
            response = requests.get(api_url, params=params, timeout=10, verify=False)
        else:
            response = requests.get(api_url, headers=header, params=params, timeout=10, verify=False)
        response.raise_for_status()
        return response.text  # Can be JSON or text data
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def api_data_loader(api_url, header, collection_name="api_data_collection"):
    """
    Fetch data from an API, process it, and store in Chroma.

    :param api_url: The API endpoint.
    :param collection_name: Name of the collection to store data.
    """
    collection, _ = init_collection(collection_name)
    
    # Fetch data from API
    data = fetch_api_data(api_url, header)
    if not data:
        print("No data received from API.")
        return
    
    # Check if data is JSON, convert to string if necessary
    try:
        data_dict = json.loads(data)
        text = json.dumps(data_dict, indent=2)  # Convert JSON to text format
    except json.JSONDecodeError:
        text = data  # Assume it's plain text if not JSON

    print(text)

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=2000)
    chunks = text_splitter.create_documents([text])

    # Generate embeddings in parallel
    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, chunks))

    # Add each chunk to Chroma
    for idx, chunk in enumerate(chunks):
        doc_id = f"{collection_name}_api_{idx}"
        collection.add(
            documents=[chunk.page_content],
            metadatas=[{'id': doc_id}],
            embeddings=[embeddings[idx]],
            ids=[str(doc_id)]
        )

    print(f"API data loaded into collection: {collection_name}. Added {len(chunks)} chunks.")

def retrieve_context(question, collection_name="foundations_of_llms", k=10):
    if collection_name not in retriever_dict:
        init_collection(collection_name)
    retriever = retriever_dict[collection_name]
    results = retriever.invoke(question)[:k]
    context = "\n\n".join([doc.page_content for doc in results])
    return context

def retrieve_from_all_collections(question, k=10):
    all_docs = []
    for c_name, retriever in retriever_dict.items():
        docs = retriever.invoke(question)[:k]
        all_docs.extend(docs)
    context = "\n\n".join([doc.page_content for doc in all_docs])
    return context

def document_loader(document, collection_name):
        if document.file.path.endswith(".pdf"):
            pdfloader(document, collection_name)
        elif document.file.path.endswith(".txt"):
            txtloader(document, collection_name)
        elif document.file.path.endswith(".json"):
            jsonloader(document, collection_name)

def init_stores():
    rag_pools = RAGPool.objects.all()
    for collection_name in rag_pools:
        if collection_name.RAGPoolName not in retriever_dict:
            init_collection(collection_name.RAGPoolName)
    
    documents = UploadedFile.objects.all()
    for document in documents:
        document_loader(document=document, collection_name=document.rag_pool.RAGPoolName)

    apis = APIData.objects.all()
    for api in apis:
        header = {
            "Authorization": f"Bearer {api.api_key}",
            "Content-Type": "application/json"
        }
        api_data_loader(api.base_url, header=header, collection_name=api.rag_pool.RAGPoolName)

init_stores()
