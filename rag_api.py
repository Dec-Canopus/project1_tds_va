from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from rag_process import complete_rag_process

app = FastAPI()

@app.post("/api/")
async def handle_rag_request(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        link = data.get("link")      # Optional
        image = data.get("image")    # Optional (can be base64 or image URL)

        if not question:
            return JSONResponse(status_code=400, content={"error": "Missing 'question' in request"})

        # Pass all inputs to the RAG pipeline
        answer, reranked_docs = complete_rag_process(question, link=link, image=image)

        return JSONResponse(content={
            "answer": answer,
            "links": [
                {
                    "text": doc.page_content,
                    "url": doc.metadata.get("url", "")
                }
                for doc, _ in reranked_docs
            ]
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/")
def blank():
    return "Error: 21f3001973 - Just a Home Page!"
