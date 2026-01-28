from langchain_core.runnables import RunnableConfig
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import graph
from typing import List
from services import create_upload_service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_service = create_upload_service()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "1"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), urls: List[str] = Form(...)):
    return await upload_service.process_uploads(files, urls)


@app.post("/chat")
async def chat(request: ChatRequest):
    config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}
    result = graph.invoke({"messages": [{"role": "user", "content": request.message}]}, config=config)
    
    # Extract the last AI message (excluding tool messages and messages with tool calls)
    messages = result.get("messages", [])
    ai_response = ""
    for msg in reversed(messages):
        # Only consider AIMessage types that don't have tool calls (internal reasoning)
        if (hasattr(msg, '__class__') and 
            msg.__class__.__name__ == 'AIMessage' and 
            hasattr(msg, 'content') and 
            msg.content and
            (not hasattr(msg, 'tool_calls') or not msg.tool_calls)):
            ai_response = msg.content
            break
    
    return {"response": ai_response}