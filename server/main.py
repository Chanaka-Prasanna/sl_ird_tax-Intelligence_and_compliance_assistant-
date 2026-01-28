from langchain_core.runnables import RunnableConfig
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ingestion import ingest_pdfs
from graph import graph
import os
import shutil
from pathlib import Path
from typing import List

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


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload PDF files, store them temporarily, ingest them into the vector store,
    and then delete the temporary directory.
    """
    # Create temporary directory for uploads
    temp_dir = Path("temp_pdfs")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Save uploaded files
        file_paths_with_urls = {}
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
            
            file_path = temp_dir / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Use filename as source URL for uploaded files
            file_paths_with_urls[str(file_path)] = f"Uploaded: {file.filename}"
        
        if not file_paths_with_urls:
            return {"message": "No valid PDF files were uploaded."}
        
        # Ingest the PDFs
        doc_count = ingest_pdfs(file_paths_with_urls)
        
        # Clean up - delete temporary directory
        shutil.rmtree(temp_dir)
        
        return {
            "message": f"Successfully ingested {doc_count} document splits from {len(file_paths_with_urls)} files.",
            "files_processed": len(file_paths_with_urls)
        }
    
    except Exception as e:
        # Clean up on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise e


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