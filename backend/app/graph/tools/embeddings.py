"""
embeddings.py — Text → vector embeddings and similarity scoring.

Two public functions:
  get_embeddings(texts)          → list of float vectors
  compute_similarity(vec_a, vec_b) → float in [0, 1]

Used by match_agent.py as a fast, cheap pre-filter before the LLM
does detailed scoring. Cosine similarity near 1.0 = very similar.

Model: sentence-transformers "all-MiniLM-L6-v2"
  - 384-dimensional embeddings
  - Runs fully locally (no API key, no cost per call)
  - ~80MB model download on first use (cached after that)
  - Fast: ~10ms per sentence on CPU
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Model loading ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_model():
    """
    Load the sentence-transformer model once and cache it for the process lifetime.

    Why @lru_cache?
    ───────────────
    Loading a transformer model takes ~1–2 seconds and allocates ~500MB RAM.
    We never want to do this more than once per process.  lru_cache(maxsize=1)
    on a no-arg function is Python's simplest singleton pattern — the result
    is cached after the first call and reused forever.

    Why lazy load (inside a function, not at module level)?
    ────────────────────────────────────────────────────────
    If we loaded at module import time, starting the FastAPI server would block
    for ~2 seconds even when embeddings aren't needed (e.g. health check route).
    Lazy loading means the cost is paid only on the first actual embedding call.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise RuntimeError(
            "sentence-transformers is not installed. Run: uv add sentence-transformers"
        ) from e

    model_name = "all-MiniLM-L6-v2"
    logger.info("Loading embedding model '%s' (first call only)...", model_name)
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded.")
    return model


# ── Public API ────────────────────────────────────────────────────────────────

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of strings into their embedding vectors.

    How it works:
      SentenceTransformer.encode() runs each string through a small BERT-family
      model and returns a fixed-size vector (384 floats for MiniLM-L6).
      Semantically similar sentences will have vectors that point in similar
      directions — that's what cosine similarity then measures.

    Args:
        texts: List of strings to embed. Can be resume summaries, JD text,
               individual sentences, or skill lists.

    Returns:
        List of float lists — one 384-dim vector per input string.
        The order matches the input list exactly.

    Example:
        vecs = get_embeddings(["5 years Python experience", "Senior Python developer"])
        # vecs[0] and vecs[1] will be very similar vectors
    """
    if not texts:
        return []

    model = _get_model()

    # encode() accepts a list and returns a numpy array of shape (N, 384).
    # .tolist() converts it to plain Python floats — easier to serialize to JSON
    # and store in PostgreSQL or pass through LangGraph state.
    embeddings = model.encode(texts, show_progress_bar=False)
    logger.debug("get_embeddings: encoded %d texts → shape %s", len(texts), embeddings.shape)

    return embeddings.tolist()


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two embedding vectors.

    Cosine similarity measures the angle between two vectors:
      - 1.0  = identical direction (semantically the same)
      - 0.0  = perpendicular (unrelated)
      - -1.0 = opposite (extremely different — rare with sentence embeddings)

    Why cosine and not Euclidean distance?
    ───────────────────────────────────────
    Euclidean distance is affected by vector magnitude (length), but embedding
    magnitude doesn't carry semantic meaning — only direction does.
    Cosine normalises away magnitude, so it purely captures semantic direction.

    Args:
        vec_a: First embedding vector (list of floats).
        vec_b: Second embedding vector, must be the same length as vec_a.

    Returns:
        Float in [-1.0, 1.0], clipped to [0.0, 1.0] for our use case.

    Raises:
        ValueError: If vectors are empty or have mismatched lengths.
    """
    if not vec_a or not vec_b:
        raise ValueError("Both vectors must be non-empty.")
    if len(vec_a) != len(vec_b):
        raise ValueError(
            f"Vector length mismatch: {len(vec_a)} vs {len(vec_b)}. "
            "Both must come from the same embedding model."
        )

    # ── Manual cosine similarity (no numpy dependency in this function) ───────
    # dot product
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    # magnitudes
    mag_a = sum(a * a for a in vec_a) ** 0.5
    mag_b = sum(b * b for b in vec_b) ** 0.5

    if mag_a == 0 or mag_b == 0:
        return 0.0  # zero vector = undefined similarity → treat as no match

    similarity = dot / (mag_a * mag_b)

    # Clip to [0, 1] — values slightly below 0 can occur due to float precision
    return max(0.0, min(1.0, similarity))


# ── Convenience: score a resume summary against a JD summary ─────────────────

def score_resume_jd(resume_text: str, jd_text: str) -> float:
    """
    One-shot helper: embed both texts and return their cosine similarity.

    This is what match_agent.py calls for a quick semantic score.
    It returns a float in [0, 1] — compare against MATCH_SCORE_THRESHOLD (0.65).

    Args:
        resume_text: Resume summary or full text.
        jd_text:     Job description text.

    Returns:
        Cosine similarity score in [0.0, 1.0].
    """
    vecs = get_embeddings([resume_text, jd_text])
    score = compute_similarity(vecs[0], vecs[1])
    logger.info("score_resume_jd: similarity = %.4f", score)
    return score
