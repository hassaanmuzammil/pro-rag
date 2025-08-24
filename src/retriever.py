from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import ParentDocumentRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from src.config import (
    PARENT_CHUNK_SIZE,
    PARENT_CHUNK_OVERLAP,
    USE_PARENT_CHILD,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

class RetrieverFactory:
    def __init__(
        self,
        vectorstore,
        docstore
    ):
        self.vectorstore = vectorstore
        self.docstore = docstore
    
    def create(
        self,
        use_parent_child: bool = USE_PARENT_CHILD,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        parent_chunk_size: int = PARENT_CHUNK_SIZE,
        parent_chunk_overlap: int = PARENT_CHUNK_OVERLAP,
        rerank: bool = True,
        model_rerank: HuggingFaceCrossEncoder = None,
        k: int = 20,
        top_n: int = 3
    ):
        if use_parent_child:
            parent_splitter = RecursiveCharacterTextSplitter(
                chunk_size=parent_chunk_size,
                chunk_overlap=parent_chunk_overlap,
            )
            child_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            base_retriever = ParentDocumentRetriever(
                vectorstore=self.vectorstore,
                docstore=self.docstore,
                parent_splitter=parent_splitter,
                child_splitter=child_splitter,
                search_kwargs={"k": k}
            )
        else:
            base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})

        if rerank and model_rerank:
            retriever = ContextualCompressionRetriever(
                base_compressor=CrossEncoderReranker(model=model_rerank, top_n=top_n),
                base_retriever=base_retriever,
            )
        else:
            retriever = base_retriever
        
        return retriever
