# main.py
import os
import uuid
import json
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from google.cloud import storage
from chunker import chunk_text
from fastapi.middleware.cors import CORSMiddleware

# — CONFIGURATION —
BUCKET_NAME = "math-pdfs"
UPLOAD_PREFIX = "uploads/"
CHUNKS_PREFIX = "chunks/"

# Initialize GCS client
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

app = FastAPI(title="PDF Upload & Chunk API")


@app.post("/upload")
async def upload_pdf(pdf: UploadFile = File(...)):
    # 1) Generate a unique ID and paths
    doc_id = str(uuid.uuid4())
    blob_name = f"{UPLOAD_PREFIX}{doc_id}.pdf"
    chunks_blob_name = f"{CHUNKS_PREFIX}{doc_id}.json"

    # 2) Upload raw PDF to GCS
    blob = bucket.blob(blob_name)
    content = await pdf.read()
    blob.upload_from_string(content, content_type=pdf.content_type)

    # 3) Parse PDF from the bytes in memory
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid PDF") from e

    # 4) Extract full text page by page
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
    text = "\n\n".join(full_text)

    # 5) Chunk the text
    chunks = chunk_text(text)

    # 6) Prepare structured JSON
    chunk_records = [
        {"id": f"{doc_id}_{i}", "text": chunk, "page": i}
        for i, chunk in enumerate(chunks, start=1)
    ]
    payload = {"doc_id": doc_id, "chunks": chunk_records}

    # 7) Upload chunks JSON to GCS
    chunks_blob = bucket.blob(chunks_blob_name)
    chunks_blob.upload_from_string(
        json.dumps(payload), content_type="application/json"
    )

    # 8) Return the doc_id for later retrieval
    return JSONResponse({"status": "ok", "doc_id": doc_id})


@app.get("/chunks/{doc_id}")
def get_chunks(doc_id: str):
    """
    Retrieve the stored chunks JSON for a given doc_id.
    """
    chunks_blob_name = f"{CHUNKS_PREFIX}{doc_id}.json"
    blob = bucket.blob(chunks_blob_name)
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    data = blob.download_as_text()
    return JSONResponse(json.loads(data))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
