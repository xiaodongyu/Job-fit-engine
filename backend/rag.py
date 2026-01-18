"""RAG utilities: parsing, chunking, embedding, FAISS index management."""
import os
import json
import uuid
import numpy as np
import faiss
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from models import UploadStatus, EvidenceChunk

import gemini_client

# === Config ===
DATA_DIR = Path("data")
JD_INDEX_PATH = DATA_DIR / "jd.index"
JD_META_PATH = DATA_DIR / "jd_meta.json"

def get_chunk_size() -> int:
    return int(os.getenv("CHUNK_SIZE", "800"))

def get_chunk_overlap() -> int:
    return int(os.getenv("CHUNK_OVERLAP", "120"))

def get_top_k() -> int:
    return int(os.getenv("TOP_K", "6"))

# === Upload tracking ===
UPLOAD_STATUS: dict[str, dict] = {}  # upload_id -> {status, detail, session_id}

# === Thread pool for background processing ===
executor = ThreadPoolExecutor(max_workers=2)


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_session_dir(session_id: str) -> Path:
    """Get session-specific directory."""
    p = DATA_DIR / "sessions" / session_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# === Parsing ===
def parse_file(file_bytes: bytes, filename: str) -> str:
    """Parse uploaded file to text. Best-effort for PDF/DOCX/TXT."""
    ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'
    
    if ext == 'txt':
        return file_bytes.decode('utf-8', errors='ignore')
    
    elif ext == 'pdf':
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text_parts = []
            
            # First try: extract text directly
            for page in doc:
                page_text = page.get_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text)
            
            result = "\n".join(text_parts)
            if result.strip():
                doc.close()
                return result
            
            # Second try: OCR for image-based/scanned PDFs
            try:
                import pytesseract
                from PIL import Image
                from io import BytesIO
                import os
                
                # Set Tesseract path for Windows if not in PATH
                if os.name == 'nt':  # Windows
                    tesseract_paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    ]
                    for tpath in tesseract_paths:
                        if os.path.exists(tpath):
                            pytesseract.pytesseract.tesseract_cmd = tpath
                            break
                
                ocr_text_parts = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    # Render page to image at 150 DPI for good OCR quality
                    mat = fitz.Matrix(150/72, 150/72)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    img = Image.open(BytesIO(img_data))
                    
                    # Run OCR
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text and ocr_text.strip():
                        ocr_text_parts.append(ocr_text)
                
                doc.close()
                result = "\n".join(ocr_text_parts)
                if result.strip():
                    return result
                raise ValueError("PDF appears to be empty (OCR found no text)")
                
            except ImportError:
                doc.close()
                raise ValueError("PDF is image-based but OCR not available. Install Tesseract OCR and run: pip install pytesseract Pillow")
            except Exception as ocr_error:
                doc.close()
                raise ValueError(f"OCR failed on image-based PDF: {ocr_error}")
                
        except ImportError as e:
            raise ValueError(f"PyMuPDF not installed. Run: pip install PyMuPDF. Error: {e}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")
    
    elif ext == 'docx':
        try:
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(file_bytes))
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
            result = "\n".join(text_parts)
            if result.strip():
                return result
            raise ValueError("DOCX appears to be empty (no extractable text)")
        except ImportError as e:
            raise ValueError(f"python-docx not installed. Run: pip install python-docx. Error: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {e}")
    
    elif ext == 'doc':
        # .doc format requires different library (not supported in MVP)
        raise ValueError(".doc format not supported. Please convert to .docx or .pdf")
    
    else:
        # Try to decode as text
        try:
            result = file_bytes.decode('utf-8', errors='ignore')
            if result.strip():
                return result
            raise ValueError("File appears to be empty")
        except Exception as e:
            raise ValueError(f"Failed to read file as text: {e}")


# === Chunking ===
def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """Split text into overlapping chunks."""
    if chunk_size is None:
        chunk_size = get_chunk_size()
    if overlap is None:
        overlap = get_chunk_overlap()
    
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


# === FAISS Index Management ===
def create_faiss_index(dim: int) -> faiss.IndexFlatIP:
    """Create a FAISS index for inner product (cosine similarity with normalized vectors)."""
    return faiss.IndexFlatIP(dim)


def save_faiss_index(index: faiss.IndexFlatIP, path: Path):
    """Save FAISS index to disk."""
    faiss.write_index(index, str(path))


def load_faiss_index(path: Path) -> Optional[faiss.IndexFlatIP]:
    """Load FAISS index from disk."""
    if path.exists():
        return faiss.read_index(str(path))
    return None


def save_metadata(meta: list[dict], path: Path):
    """Save chunk metadata to JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_metadata(path: Path) -> list[dict]:
    """Load chunk metadata from JSON."""
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


# === JD Index (Global) ===
def ingest_jds(items: list[dict]) -> int:
    """
    Ingest JD items into global FAISS index.
    items: list of {title, role, level, text}
    Returns count of chunks added.
    """
    ensure_data_dir()
    
    # Load existing index and metadata
    existing_index = load_faiss_index(JD_INDEX_PATH)
    existing_meta = load_metadata(JD_META_PATH)
    
    all_chunks = []
    all_meta = []
    
    for item in items:
        text = item["text"]
        chunks = chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"jd_{item['role']}_{item['level']}_{uuid.uuid4().hex[:8]}_{i}"
            all_chunks.append(chunk)
            all_meta.append({
                "chunk_id": chunk_id,
                "text": chunk,
                "source_type": "jd",
                "doc_id": item.get("title", "unknown"),
                "role": item["role"],
                "level": item["level"],
                "title": item.get("title", "")
            })
    
    if not all_chunks:
        return 0
    
    # Embed chunks
    embeddings = gemini_client.embed_texts(all_chunks)
    embeddings_np = np.array(embeddings, dtype=np.float32)
    
    dim = embeddings_np.shape[1]
    
    # Create or extend index
    if existing_index is None:
        index = create_faiss_index(dim)
    else:
        index = existing_index
    
    index.add(embeddings_np)
    
    # Merge metadata
    combined_meta = existing_meta + all_meta
    
    # Save
    save_faiss_index(index, JD_INDEX_PATH)
    save_metadata(combined_meta, JD_META_PATH)
    
    return len(all_chunks)


def search_jd_index(query: str, role: str = None, top_k: int = None) -> list[EvidenceChunk]:
    """Search global JD index."""
    if top_k is None:
        top_k = get_top_k()
    
    index = load_faiss_index(JD_INDEX_PATH)
    meta = load_metadata(JD_META_PATH)
    
    if index is None or not meta:
        return []
    
    # Embed query
    query_vec = gemini_client.embed_single(query)
    query_np = np.array([query_vec], dtype=np.float32)
    
    # Search
    k = min(top_k * 3, index.ntotal)  # Over-fetch for filtering
    scores, indices = index.search(query_np, k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(meta):
            continue
        m = meta[idx]
        # Filter by role if specified
        if role and m.get("role") != role:
            continue
        results.append(EvidenceChunk(
            chunk_id=m["chunk_id"],
            text=m["text"],
            source="jd",
            score=float(score)
        ))
        if len(results) >= top_k:
            break
    
    return results


# === Resume Index (Per-session) ===
def update_upload_status(upload_id: str, status: UploadStatus, detail: str = ""):
    """Update upload status."""
    if upload_id in UPLOAD_STATUS:
        UPLOAD_STATUS[upload_id]["status"] = status
        UPLOAD_STATUS[upload_id]["detail"] = detail


def get_upload_status(upload_id: str) -> dict:
    """Get upload status."""
    return UPLOAD_STATUS.get(upload_id, {"status": UploadStatus.ERROR, "detail": "Unknown upload_id"})


def process_resume_background(
    upload_id: str,
    session_id: str,
    text: str
):
    """Background task to process resume: chunk -> embed -> index."""
    try:
        session_dir = get_session_dir(session_id)
        index_path = session_dir / "resume.index"
        meta_path = session_dir / "resume_meta.json"
        
        # Step 1: Chunking
        update_upload_status(upload_id, UploadStatus.CHUNKING, "Splitting text into chunks...")
        chunks = chunk_text(text)
        
        if not chunks:
            update_upload_status(upload_id, UploadStatus.ERROR, "No text content found")
            return
        
        # Step 2: Embedding
        update_upload_status(upload_id, UploadStatus.EMBEDDING, f"Embedding {len(chunks)} chunks...")
        embeddings = gemini_client.embed_texts(chunks)
        embeddings_np = np.array(embeddings, dtype=np.float32)
        
        # Step 3: Build metadata
        meta = []
        for i, chunk in enumerate(chunks):
            meta.append({
                "chunk_id": f"resume_{session_id}_{i}",
                "text": chunk,
                "source_type": "resume",
                "session_id": session_id,
                "chunk_index": i
            })
        
        # Step 4: Build FAISS index
        update_upload_status(upload_id, UploadStatus.INDEXING, "Building search index...")
        dim = embeddings_np.shape[1]
        index = create_faiss_index(dim)
        index.add(embeddings_np)
        
        # Save
        save_faiss_index(index, index_path)
        save_metadata(meta, meta_path)
        
        # Done
        update_upload_status(upload_id, UploadStatus.READY, f"Indexed {len(chunks)} chunks")
        
    except Exception as e:
        update_upload_status(upload_id, UploadStatus.ERROR, str(e))


def start_resume_processing(session_id: str, text: str) -> str:
    """
    Start background processing of resume.
    Returns upload_id.
    """
    upload_id = uuid.uuid4().hex[:12]
    
    # Initialize status
    UPLOAD_STATUS[upload_id] = {
        "status": UploadStatus.PARSING,
        "detail": "Processing uploaded content...",
        "session_id": session_id
    }
    
    # Submit to thread pool
    executor.submit(process_resume_background, upload_id, session_id, text)
    
    return upload_id


def search_resume_index(session_id: str, query: str, top_k: int = None) -> list[EvidenceChunk]:
    """Search session's resume index."""
    if top_k is None:
        top_k = get_top_k()
    
    session_dir = get_session_dir(session_id)
    index_path = session_dir / "resume.index"
    meta_path = session_dir / "resume_meta.json"
    
    index = load_faiss_index(index_path)
    meta = load_metadata(meta_path)
    
    if index is None or not meta:
        return []
    
    # Embed query
    query_vec = gemini_client.embed_single(query)
    query_np = np.array([query_vec], dtype=np.float32)
    
    # Search
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_np, k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(meta):
            continue
        m = meta[idx]
        results.append(EvidenceChunk(
            chunk_id=m["chunk_id"],
            text=m["text"],
            source="resume",
            score=float(score)
        ))
    
    return results


def session_is_ready(session_id: str) -> bool:
    """Check if session's resume index is ready."""
    session_dir = get_session_dir(session_id)
    index_path = session_dir / "resume.index"
    return index_path.exists()


def get_all_resume_chunks(session_id: str) -> list[dict]:
    """
    Retrieve all resume chunks for a session (without search/query).
    Returns list of {chunk_id, text, source_type, session_id, chunk_index}.
    """
    session_dir = get_session_dir(session_id)
    meta_path = session_dir / "resume_meta.json"
    
    if not meta_path.exists():
        return []
    
    return load_metadata(meta_path)


# === Temporary JD processing (for user-pasted JD) ===
def search_temp_jd(jd_text: str, query: str, top_k: int = None) -> list[EvidenceChunk]:
    """
    Create temporary in-memory index for user-pasted JD and search.
    """
    if top_k is None:
        top_k = get_top_k()
    
    # Chunk the JD text
    chunks = chunk_text(jd_text)
    if not chunks:
        return []
    
    # Embed chunks
    embeddings = gemini_client.embed_texts(chunks)
    embeddings_np = np.array(embeddings, dtype=np.float32)
    
    # Build temp index
    dim = embeddings_np.shape[1]
    index = create_faiss_index(dim)
    index.add(embeddings_np)
    
    # Embed query and search
    query_vec = gemini_client.embed_single(query)
    query_np = np.array([query_vec], dtype=np.float32)
    
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_np, k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunks):
            continue
        results.append(EvidenceChunk(
            chunk_id=f"temp_jd_{idx}",
            text=chunks[idx],
            source="jd",
            score=float(score)
        ))
    
    return results
