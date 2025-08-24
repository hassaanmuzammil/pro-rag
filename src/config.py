import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

### start .env

# MinIO
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "default")

# Qdrant
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "default")

# LLM
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

# Chainlit
CHAINLIT_DB_URL = os.environ.get("CHAINLIT_DB_URL", "postgres:password@localhost:5432/chainlit")
CHAINLIT_AUTH_SECRET = os.environ.get("CHAINLIT_AUTH_SECRET", "supersecret")

# Postgres
POSTGRES_URL = os.environ.get("POSTGRES_URL", "postgres:password@localhost:5432/store")

# Other
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
PORT = int(os.environ.get("PORT", "8000"))

### end .env

# other params
ALLOWED_EXTENSIONS = [".pdf", ".txt", ".docx"]

EMBEDDING_SIZE = 384
DENSE_MODEL = "all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"
RERANKING_MODEL = "jinaai/jina-reranker-v2-base-multilingual"

# EMBEDDING_SIZE = 1024
# DENSE_MODEL = "Qwen/Qwen3-Embedding-0.6B"
# SPARSE_MODEL = "naver/splade-cocondenser-ensembledistil"
# RERANKING_MODEL = "Qwen/Qwen3-Reranker-0.6B"

PARENT_CHUNK_SIZE = 2000
PARENT_CHUNK_OVERLAP = 100
USE_PARENT_CHILD = True
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

BASE_MODEL="gpt-3.5-turbo-instruct"
NUM_CTX=20480
NUM_PREDICT=2048
STOP_TOKENS = [
    "</s>",
    "<|im_end|>",
    "<|eot_id|>",
    "<|endoftext|>",
]

TEMPLATE_FINAL_ANSWER="templates/final_answer.txt"
TEMPLATE_QUERY_REWRITE="templates/query_rewrite.txt"
TEMPLATE_CONTEXT_RELEVANCE="templates/context_relevance.txt"
