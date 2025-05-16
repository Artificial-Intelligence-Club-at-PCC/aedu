# cloud-parser/main.py

import os
import uuid
import json
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from google.oauth2 import service_account
from google.cloud import storage

from .chunker import chunk_text  # relative import

# — CONFIGURATION —
BUCKET_NAME   = "math-pdfs"
UPLOAD_PREFIX = "uploads/"
CHUNKS_PREFIX = "chunks/"

# — CREDENTIALS & CLIENT SETUP —

# 1) Path to your service account JSON
#    You can also set GOOGLE_APPLICATION_CREDENTIALS in your shell instead.
KEY_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "cloud-parser/savvy-hull-453721-i4-c516ba625444.json"
)

# 2) Load the service account credentials
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)

# 3) Initialize the GCS client with explicit credentials & project
storage_client = storage.Client(
    credentials=credentials,
    project=credentials.project_id
)

# 4) Grab your bucket
bucket = storage_client.bucket(BUCKET_NAME)

# — FASTAPI SETUP —

app = FastAPI(title="PDF Upload & Chunk API")

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_pdf(pdf: UploadFile = File(...)):
    # 1) Generate unique ID and blob names
    doc_id             = str(uuid.uuid4())
    blob_name          = f"{UPLOAD_PREFIX}{doc_id}.pdf"
    chunks_blob_name   = f"{CHUNKS_PREFIX}{doc_id}.json"

    # 2) Upload raw PDF
    blob    = bucket.blob(blob_name)
    content = await pdf.read()
    blob.upload_from_string(content, content_type=pdf.content_type)

    # 3) Parse PDF
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid PDF") from e

    # 4) Extract text
    full_text = [page.get_text() for page in doc]
    text      = "\n\n".join(full_text)

    # 5) Chunk it
    chunks = chunk_text(text)

    # 6) Build JSON structure
    chunk_records = [
        {"id": f"{doc_id}_{i}", "text": chunk, "page": i}
        for i, chunk in enumerate(chunks, start=1)
    ]
    payload = {"doc_id": doc_id, "chunks": chunk_records}

    # 7) Upload chunks JSON
    chunks_blob = bucket.blob(chunks_blob_name)
    chunks_blob.upload_from_string(
        json.dumps(payload),
        content_type="application/json"
    )

    # 8) Return the document ID
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
