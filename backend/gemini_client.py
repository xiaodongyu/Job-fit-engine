"""Gemini API client for embeddings and generation."""
import os
import json
from google import genai
from google.genai import types

_client: genai.Client = None


def get_client() -> genai.Client:
    """Get or create Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        _client = genai.Client(api_key=api_key)
    return _client


def get_embed_model() -> str:
    """Get embedding model name from env."""
    return os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")


def get_gen_model() -> str:
    """Get generation model name from env."""
    return os.getenv("GEMINI_GEN_MODEL", "gemini-2.0-flash")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using Gemini embedding model.
    Returns list of embedding vectors (normalized for cosine similarity).
    """
    if not texts:
        return []
    
    client = get_client()
    model = get_embed_model()
    
    embeddings = []
    # Process in batches to avoid rate limits
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.models.embed_content(
            model=model,
            contents=batch
        )
        for emb in response.embeddings:
            vec = emb.values
            # Normalize for cosine similarity (FAISS IndexFlatIP)
            norm = sum(x * x for x in vec) ** 0.5
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
    
    return embeddings


def embed_single(text: str) -> list[float]:
    """Embed a single text."""
    result = embed_texts([text])
    return result[0] if result else []


def generate(
    system_prompt: str,
    user_prompt: str,
    json_schema: dict = None
) -> dict:
    """
    Generate text using Gemini.
    If json_schema provided, request JSON output.
    Returns {"content": parsed_json_or_text, "raw": raw_text}
    """
    client = get_client()
    model = get_gen_model()
    
    # Build config
    config = {}
    if json_schema:
        config["response_mime_type"] = "application/json"
        config["response_schema"] = json_schema
    
    # Combine prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(**config) if config else None
    )
    
    raw_text = response.text if response.text else ""
    
    result = {"content": None, "raw": raw_text}
    
    if json_schema and raw_text:
        try:
            result["content"] = json.loads(raw_text)
        except json.JSONDecodeError:
            result["content"] = {"error": "Failed to parse JSON", "raw": raw_text}
    else:
        result["content"] = raw_text
    
    return result
