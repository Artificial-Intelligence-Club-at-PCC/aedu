# chunker.py

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100):
    """
    Splits `text` into overlapping chunks of roughly `chunk_size` words,
    overlapping by `overlap` words between chunks.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
