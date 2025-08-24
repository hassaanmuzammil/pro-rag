from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore, RetrievalMode

from src.logger import logger
from src.db.session import SyncSessionFactory, AsyncSessionFactory
from src.minio_client import MinioClient
from src.qdrant import create_collection
from src.loader import FileLoader
from src.docstore import PostgresStore
from src.retriever import RetrieverFactory
from src.models import model_dense, model_sparse, model_rerank
from src.rag import RAGPipeline
from src.llm import LLMProcessor
from src.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    EMBEDDING_SIZE,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    LLM_BASE_URL,
    LLM_API_KEY,
    BASE_MODEL,
    NUM_CTX,
    NUM_PREDICT,
)

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    prefer_grpc=True,
)
create_collection(
    client=qdrant_client,
    collection_name=QDRANT_COLLECTION,
    embedding_size=EMBEDDING_SIZE
)

mc = MinioClient(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

loader = FileLoader()

retrieval_mode = "hybrid"
retrieval_mode_mapping = {
    "dense": RetrievalMode.DENSE,
    "sparse": RetrievalMode.SPARSE,
    "hybrid": RetrievalMode.HYBRID
}
vectorstore = QdrantVectorStore(
    client=qdrant_client,
    collection_name=QDRANT_COLLECTION,
    embedding=model_dense,
    sparse_embedding=model_sparse,
    retrieval_mode=retrieval_mode_mapping.get("retrieval_mode", RetrievalMode.HYBRID),
    vector_name="dense",
    sparse_vector_name="sparse"
)

docstore = PostgresStore(
    sync_session_factory=SyncSessionFactory,
    async_session_factory=AsyncSessionFactory
)

retriever_factory = RetrieverFactory(
    vectorstore=vectorstore,
    docstore=docstore
)
# query_retriever = retriever_factory.create(rerank=True, model_rerank=model_rerank)
query_retriever = retriever_factory.create(rerank=False) # for faster testing
index_retriever = retriever_factory.create(rerank=False)

processor = LLMProcessor(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=BASE_MODEL,
    num_ctx=NUM_CTX,
    num_predict=NUM_PREDICT
)

pipeline = RAGPipeline(
    loader=loader,
    vectorstore=vectorstore,
    docstore=docstore,
    query_retriever=query_retriever,
    index_retriever=index_retriever,
    processor=processor
)