# 🔍 FastAPI RAG Application

This project provides a simple **Retrieval-Augmented Generation (RAG)** API using **FastAPI**, powered by:

- 🧠 OpenAI / AIPipe (for LLMs)
- 📚 Pinecone (for vector storage & retrieval)
- 🔍 LangSmith (for tracing & observability)
- 📦 Optional OCR (Tesseract or image input support)

---

## 📁 Project Structure

├── data/
│ └── combined_data.json # 
├── rag_api.py # FastAPI app entry point
├── rag_process.py # Core logic for RAG pipeline
├── requirements.txt # Python dependencies
├── vercel.json # Vercel deployment config
└── README.md # This file


---

## 🚀 Getting Started (Local Setup)

### 1. Clone the Repository

git clone https://github.com/Dec-Canopus/project1_tds_va.git
cd project1_tds_va

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate


pip install -r requirements.txt

## Configure Environment Variables
Create a .env file in the root directory and add the following:

# OpenAI or AIPipe (required)
OPENAI_API_KEY=your-openai-or-aipipe-key

# LangSmith (optional)
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=your-project-name

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENV=your-pinecone-environment
PINECONE_INDEX=your-pinecone-index

✅ You may also create a .env.example file and share it with your team.

## Run the API Server
uvicorn rag_api:app --reload
Visit: http://127.0.0.1:8000

Endpoint: POST /api/
✅ Request Body
{
  "question": "What is the reference book for TDS?",
  "link": "Optional URL for context",
  "image": "Optional base64 string or image URL"
}
🔁 Response Example
{
  "answer": "There are no IITM certified books...",
  "links": [
  {
      "text": "there are no IITM certified books nor PDFs...",
      "url": "https://discourse.onlinedegree.iitm.ac.in/t/tds-iitm-certified-books/163147"
    }
  ]
}
