from typing import Literal, Optional, AsyncGenerator
from typing_extensions import TypeAlias
from langchain_core.documents import Document
from langchain_core.runnables import Runnable
from langchain_qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.loader import FileLoader
from src.docstore import PostgresStore
from src.llm import LLMProcessor

RetrieverInput: TypeAlias = str
RetrieverOutput: TypeAlias = list[Document]
RetrieverLike: TypeAlias = Runnable[RetrieverInput, RetrieverOutput]

class RAGPipeline:
    def __init__(
        self,
        processor: LLMProcessor,
        loader: FileLoader,
        vectorstore: QdrantVectorStore,
        use_parent_child: bool = True,
        query_retriever: Optional[RetrieverLike] = None,
        index_retriever: Optional[RetrieverLike] = None,
        docstore: Optional[PostgresStore] = None,
        splitter: Optional[RecursiveCharacterTextSplitter] = None,
    ):
        self.processor = processor
        self.loader = loader
        self.vectorstore = vectorstore
        self.docstore = docstore        

        self.use_parent_child = use_parent_child
        if not use_parent_child:
            self.splitter = splitter
            self.query_retriever = vectorstore.as_retriever()
        # Note: Index and query retrievers are separate because
        # ContextualCompressionRetriever supports only retrieval (no add_documents),
        # whereas ParentDocumentRetriever supports both indexing and retrieval.
        self.query_retriever = query_retriever
        self.index_retriever = index_retriever or query_retriever

    def load(self, file_path: str, mode: Literal["single", "page"] = "page") -> list[Document]:
        documents = self.loader.load(file_path=file_path, mode=mode)
        return documents   

    def _split(self, documents: list[Document]) -> list[Document]:
        if not self.splitter:
            raise ValueError("Splitter must be provided when use_parent_child=False")
        documents = self.splitter.split_documents(documents)
        return documents

    async def index(self, documents: list[Document]) -> None:
        if self.use_parent_child:
            await self.index_retriever.aadd_documents(documents)
        else:
            documents = self._split(documents)
            await self.vectorstore.aadd_documents(documents)

    async def _expand_with_neighbors(
        self,
        documents: list[Document]
    ) -> list[Document]:
        """
        Expands the document list by including ±1 neighbors from docstore.
        """
        if not self.docstore:
            return documents
        seen = set()
        expanded = []
        for doc in documents:
            current_key = await self.docstore.aget_key_by_value(doc)
            if current_key and current_key not in seen:
                seen.add(current_key)
                expanded.append(doc)
            for key_field in ["prev_key", "next_key"]:
                key = doc.metadata.get(key_field)
                if key and key not in seen:
                    neighbor_docs = await self.docstore.amget((key,))
                    if neighbor_docs:
                        seen.add(key)
                        expanded.append(neighbor_docs[0])
        return expanded

    async def retrieve(self, query: str, expand_context: bool = False) -> list[dict]:
        """
        Retrieve documents relevant to a query.
        
        Args:
            query (str): The query string.
            expand_context (bool): If True, also include ±1 neighboring documents.
        Returns:
            list[dict]: Structured and sorted documents data.
        """
        documents = await self.query_retriever.ainvoke(query)
        if expand_context:
            documents = await self._expand_with_neighbors(documents)
        seen = set()
        sources = []
        for doc in documents:
            key = await self.docstore.aget_key_by_value(doc)
            if key not in seen:
                seen.add(key)
                sources.append({
                    "name": doc.metadata.get("source", "Unknown").split("/")[-1],
                    "page": doc.metadata.get("page_label") or doc.metadata.get("page"),
                    "order": doc.metadata.get("order"),
                    "content": doc.page_content.strip(),
                })
        sources.sort(key=lambda x: (x.get("name", ""), x.get("order")))
        for s in sources:
            s.pop("order", None)
        return sources

    async def generate(
        self,
        message: str,
        chat_history: Optional[list[dict]] = None,
        expand_context: bool = False
    ) -> AsyncGenerator[str, None]:       

        rewritten_query, fallback_message = await self.processor.query_rewrite(message, chat_history)
        if not rewritten_query:
            yield fallback_message
            return
        sources = await self.retrieve(
            query=rewritten_query,
            expand_with_neighbors=expand_context
        )
        context = self.processor.build_context(sources)
        async for chunk in self.processor.final_answer(rewritten_query, context):
            yield chunk
