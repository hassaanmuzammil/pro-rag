from sentence_transformers import SparseEncoder
from langchain_qdrant.sparse_embeddings import SparseVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from src.config import DENSE_MODEL, SPARSE_MODEL, RERANKING_MODEL

class SparseEncoderWrapper:
    """
    A wrapper around sentence-transformers' SparseEncoder that standardizes the interface
    to match FastEmbedSparse, making it compatible with Qdrant and LangChain's expected
    sparse embedding APIs.

    This wrapper provides:
        - embed_query(str) -> SparseVector
        - embed_documents(list[str]) -> list[SparseVector]
    
    Outputs are converted into SparseVector format with explicit indices and values,
    ensuring consistency with other sparse retrievers like FastEmbedSparse.
    """
    def __init__(self, model_name: str):
        self.model = SparseEncoder(model_name)
    
    def embed_query(self, query: str):
        result = self.model.encode_query(query).coalesce()
        return SparseVector(
            indices=result.indices()[0].tolist(),
            values=result.values().tolist()
        )
    
    def embed_documents(self, docs: list[str]):
        batched = self.model.encode_documents(docs)
        row_indices = batched.indices()[0]
        col_indices = batched.indices()[1]
        values = batched.values()

        num = batched.size(0)
        vectors = [[] for _ in range(num)]

        for id, token_id, value in zip(row_indices, col_indices, values):
            vectors[id.item()].append((token_id.item(), value.item()))
        
        return [
            SparseVector(
                indices=[idx for idx, _ in vector],
                values=[val for _, val in vector]
            )
            for vector in vectors
        ]

# model_sparse = SparseEncoderWrapper(model_name=SPARSE_MODEL)
model_sparse = FastEmbedSparse(model_name=SPARSE_MODEL)
model_dense = HuggingFaceEmbeddings(model_name=DENSE_MODEL)
model_rerank = HuggingFaceCrossEncoder(model_name=RERANKING_MODEL, model_kwargs={"trust_remote_code": True})

# Fix for "ValueError: Cannot handle batch_size > 1 if no padding token is defined"
if not model_rerank.client.model.config.pad_token_id:
    model_rerank.client.model.config.pad_token_id = model_rerank.client.tokenizer.pad_token_id
