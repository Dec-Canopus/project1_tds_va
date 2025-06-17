import os
import json
import requests
import base64
from io import BytesIO
from PIL import Image
import pytesseract
from urllib.parse import urlparse
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.load import dumps, loads
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings

pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\gsing\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'


load_dotenv()

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "articles-tds-project1"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

llm = ChatOpenAI(temperature=0)

def generate_queries_from_aipipe(question):
    url = "https://aipipe.org/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": f"Generate five different perspectives on this question: {question}"}],
        "model": "gpt-3.5-turbo"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        generated_queries = response_data["choices"][0]["message"]["content"].split("\n")
        return [query.strip() for query in generated_queries]
    else:
        print("Error in generating queries from AIPipe:", response.text)
        return []

def retrieve_documents(queries):
    documents = []
    
    for query in queries:
        results = vector_store.similarity_search(query, k=5)
        # print(results)
        documents.append([doc for doc in results])
    
    return documents

def reciprocal_rank_fusion(results: list[list], k=60):
    fused_scores = {}
    
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            fused_scores[doc_str] += 1 / (rank + k)
    
    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]
    print(reranked_results)
    
    return reranked_results

def generate_answer_with_rag_fusion(query, docs, extra_context=""):
    context = "\n".join([doc.page_content for doc, _ in docs])
    full_context = context + "\n\n" + extra_context if extra_context else context

    prompt_template = """"You are a helpful Virtual TA for the Tools for Data Science (TDS) course.
    Answer the following question based on this context:

    {context}

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    answer_chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = answer_chain.invoke({"context": full_context, "question": query})
    return answer

def extract_text_from_image_input(image_input):
    try:
        if image_input.startswith("http"):
            # Load image from URL
            response = requests.get(image_input)
            if response.status_code != 200:
                print("⚠️ Failed to fetch image from URL")
                return None
            image = Image.open(BytesIO(response.content))
        else:
            # Assume it's base64
            decoded = base64.b64decode(image_input)
            image = Image.open(BytesIO(decoded))

        text = pytesseract.image_to_string(image)
        print("📸 Extracted Text from Image:\n", text.strip())
        return text.strip()

    except Exception as e:
        print("❌ Error extracting image text:", str(e))
        return None

def complete_rag_process(question, link=None, image=None):
    extra_context = ""

    # Step 1: Extract text from image if provided
    if image:
        print("🖼️ Trying to extract text from image...")
        extracted_image_text = extract_text_from_image_input(image)
        if extracted_image_text:
            extra_context += f"\n\n[Image Text]\n{extracted_image_text}"

    # Step 2: If link is provided, attempt vector search and add content to context
    if link:
        print(f"🔗 Searching using provided link: {link}")
        link_results = vector_store.similarity_search(link, k=5)
        if link_results:
            reranked_link_docs = [(doc, 1.0) for doc in link_results]  # dummy score
            link_context = "\n".join(doc.page_content for doc, _ in reranked_link_docs)
            extra_context += f"\n\n[Link Context]\n{link_context}"
        else:
            print("⚠️ No documents found for the link. Continuing with standard RAG.")

    # Step 3: Standard RAG with multi-query + fusion
    generated_queries = generate_queries_from_aipipe(question)
    if not generated_queries:
        print("❌ No queries generated from AIPipe.")
        return "Could not generate queries", []

    documents = retrieve_documents(generated_queries)
    reranked_docs = reciprocal_rank_fusion(documents)

    answer = generate_answer_with_rag_fusion(question, reranked_docs, extra_context=extra_context)
    return answer, reranked_docs


# # Example usage
# question = "Should I use docker or Podman for the course?"
# final_answer = complete_rag_process(question)
# print(final_answer)