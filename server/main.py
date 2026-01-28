from langchain_core.runnables import RunnableConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ingestion import ingest_pdfs
from graph import graph

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "1"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/ingest")
async def ingest():
    # Map file paths to their original source URLs
    file_paths_with_urls = {
        "pdfs/Asmt_CIT_003_2022_2023_E.pdf": "https://www.ird.gov.lk/en/Downloads/IT_Corporate_Doc/Asmt_CIT_003_2022_2023_E.pdf",
        "pdfs/PN_IT_2025-01_26032025_E.pdf": "https://www.ird.gov.lk/en/Lists/Latest%20News%20%20Notices/Attachments/666/PN_IT_2025-01_26032025_E.pdf",
        "pdfs/SET_25_26_Detail_Guide_E.pdf": "https://www.ird.gov.lk/ta/Downloads/IT_SET_Doc/SET_25_26_Detail_Guide_E.pdf"
    }
    doc_lengths = ingest_pdfs(file_paths_with_urls)
    return {"message": f"Ingested {doc_lengths} document splits."}


@app.post("/chat")
async def chat(request: ChatRequest):
    config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}
    result = graph.invoke({"messages": [{"role": "user", "content": request.message}]}, config=config)
    
    # Extract the last AI message
    messages = result.get("messages", [])
    ai_response = ""
    for msg in reversed(messages):
        if hasattr(msg, 'content') and msg.content:
            ai_response = msg.content
            break
    
    return {"response": ai_response}