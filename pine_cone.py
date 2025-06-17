from pinecone import Pinecone
from pinecone import ServerlessSpec
import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

load_dotenv()

pinecone_api_key = os.environ.get("PINECONE_API_KEY")
os.environ["LANGSMITH_TRACING"] = "true"

pc = Pinecone(api_key=pinecone_api_key)

index_name = "articles-tds-project1"

if not pc.has_index(index_name):
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

index = pc.Index(index_name)

embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

json_file_path = "data/combined_data.json" 
with open(json_file_path, 'r', encoding='utf-8') as f:
    documents_data = json.load(f)


def split_text_into_chunks(text, max_length=4000):
    """Split text into chunks by adding content until exceeding max length."""
    chunks = []
    current_chunk = ""

    for paragraph in text.split("\n"): 
        
        if len(current_chunk) + len(paragraph) + 1 <= max_length:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def calculate_batch_size(documents):
    total_size = sum(len(doc.page_content) for doc in documents)
    return total_size


def add_documents_in_batches(documents, ids, max_size=4000000):
    batch_sizes = [30, 15, 5, 1]
    
    i = 0
    while i < len(documents):
        for batch_size in batch_sizes:
            batch_documents = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            
            total_size = calculate_batch_size(batch_documents)
            
            if total_size <= max_size:
                vector_store.add_documents(documents=batch_documents, ids=batch_ids)
                print(f"Added {len(batch_documents)} documents to Pinecone (batch size {batch_size}).")
                i += batch_size
                break
        else:
            batch_documents = documents[i:i + 1]
            batch_ids = ids[i:i + 1]
            vector_store.add_documents(documents=batch_documents, ids=batch_ids)
            print(f"Added 1 document to Pinecone (batch size 1).")
            i += 1


documents = []
ids = []

for i, doc_data in enumerate(documents_data):
    title = doc_data.get('title')
    content = doc_data.get('content')
    url = doc_data.get('url')

    content_chunks = split_text_into_chunks(content)

    for chunk_index, chunk in enumerate(content_chunks):
        document = Document(page_content=chunk, metadata={"title": title, "url": url, "chunk_index": chunk_index})
        documents.append(document)
        ids.append(f"{i+1}_{chunk_index+1}")

add_documents_in_batches(documents, ids)

print(f"Successfully added {len(documents)} document chunks to Pinecone.")
