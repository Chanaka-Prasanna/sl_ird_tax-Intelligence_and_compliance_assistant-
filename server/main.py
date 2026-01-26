from fastapi import FastAPI
from ingestion import ingest_pdfs
from tools import retriever_tool

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/ingest")
async def ingest():
    file_paths = [
        "pdfs/Asmt_CIT_003_2022_2023_E.pdf",
        "pdfs/PN_IT_2025-01_26032025_E.pdf",
        "pdfs/SET_25_26_Detail_Guide_E.pdf"
    ]
    doc_lengths = ingest_pdfs(file_paths)
    return {"message": f"Ingested {doc_lengths} document splits."}


@app.get("/chat")
async def chat(query: str):
    result = retriever_tool.invoke({"query": query})
    return {"result": result}