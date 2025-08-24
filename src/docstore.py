from typing import Dict, Optional, Generic, Iterator, Sequence, TypeVar, AsyncIterator
from sqlalchemy import select, delete, cast, Integer
from sqlalchemy.orm import sessionmaker
from langchain_core.documents import Document
from langchain_core.stores import BaseStore

from src.logger import logger
from src.db.models import DocumentModel, SQLDocument

D = TypeVar("D", bound=Document)


class PostgresStore(BaseStore[str, DocumentModel], Generic[D]):
    def __init__(
        self,
        sync_session_factory: sessionmaker,
        async_session_factory: sessionmaker,
        link_documents: bool = True,
    ):
        self.SyncSession = sync_session_factory
        self.AsyncSession = async_session_factory
        self.link_documents = link_documents

    def serialize_document(self, doc: Document) -> dict:
        return {"page_content": doc.page_content, "metadata": doc.metadata}

    def deserialize_document(self, value: dict) -> Document:
        return Document(
            page_content=value.get("page_content", ""),
            metadata=value.get("metadata", {}),
        )

    def mget(self, keys: Sequence[str]) -> list[Document]:
        with self.SyncSession() as session:
            try:
                sql_documents = (
                    session.query(SQLDocument).filter(SQLDocument.key.in_(keys)).all()
                )
                return [
                    self.deserialize_document(sql_doc.value)
                    for sql_doc in sql_documents
                ]
            except Exception as e:
                logger.error(f"Error in mget: {e}")
                session.rollback()
                return []

    async def amget(self, keys: Sequence[str]) -> list[Document]:
        async with self.AsyncSession() as session:
            try:
                stmt = select(SQLDocument).where(SQLDocument.key.in_(keys))
                result = await session.execute(stmt)
                sql_documents = result.scalars().all()
                return [
                    self.deserialize_document(sql_doc.value)
                    for sql_doc in sql_documents
                ]
            except Exception as e:
                logger.error(f"Error in amget: {e}")
                await session.rollback()
                return []

    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        with self.SyncSession() as session:
            try:
                serialized_docs = []
                for i, (key, document) in enumerate(key_value_pairs):
                    serialized_doc = self.serialize_document(document)
                    # store prev and next document keys in metadata, also store order
                    if self.link_documents:
                        prev_key = key_value_pairs[i - 1][0] if i > 0 else None
                        next_key = (
                            key_value_pairs[i + 1][0]
                            if i < len(key_value_pairs) - 1
                            else None
                        )
                        metadata = serialized_doc.get("metadata", {})
                        metadata["prev_key"] = prev_key
                        metadata["next_key"] = next_key
                        metadata["order"] = i
                        serialized_doc["metadata"] = metadata
                    serialized_docs.append((key, serialized_doc))
                documents_to_update = [
                    SQLDocument(key=key, value=value) for key, value in serialized_docs
                ]
                session.bulk_save_objects(documents_to_update, update_changed_only=True)
                session.commit()
            except Exception as e:
                logger.error(f"Error in mset: {e}")
                session.rollback()

    async def amset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        async with self.AsyncSession() as session:  # Session is async sessionmaker
            try:
                serialized_docs = []
                for i, (key, document) in enumerate(key_value_pairs):
                    serialized_doc = self.serialize_document(document)
                    # store prev and next document keys in metadata, also store order
                    if self.link_documents:
                        prev_key = key_value_pairs[i - 1][0] if i > 0 else None
                        next_key = (
                            key_value_pairs[i + 1][0]
                            if i < len(key_value_pairs) - 1
                            else None
                        )
                        metadata = serialized_doc.get("metadata", {})
                        metadata["prev_key"] = prev_key
                        metadata["next_key"] = next_key
                        metadata["order"] = i
                        serialized_doc["metadata"] = metadata
                    serialized_docs.append((key, serialized_doc))
                documents_to_update = [
                  SQLDocument(key=key, value=value) for key, value in serialized_docs
                ]
                # Use async bulk operations or add_all + await flush
                session.add_all(documents_to_update)
                await session.commit()
            except Exception as e:
                logger.error(f"Error in amset: {e}")
                await session.rollback()

    def mdelete(self, keys: Sequence[str]) -> None:
        with self.SyncSession() as session:
            try:
                session.query(SQLDocument).filter(SQLDocument.key.in_(keys)).delete(
                    synchronize_session=False
                )
                session.commit()
            except Exception as e:
                logger.error(f"Error in mdelete: {e}")
                session.rollback()

    async def amdelete(self, keys: Sequence[str]) -> None:
        async with self.AsyncSession() as session:
            try:
                stmt = delete(SQLDocument).where(SQLDocument.key.in_(keys))
                await session.execute(stmt)
                await session.commit()
            except Exception as e:
                logger.error(f"Error in amdelete: {e}")
                await session.rollback()

    def yield_keys(self, *, prefix: Optional[str] = None) -> Iterator[str]:
        with self.SyncSession() as session:
            try:
                query = session.query(SQLDocument.key)
                if prefix:
                    query = query.filter(SQLDocument.key.like(f"{prefix}%"))
                for key in query:
                    yield key[0]
            except Exception as e:
                logger.error(f"Error in yield_keys: {e}")
                session.rollback()

    async def ayield_keys(self, *, prefix: Optional[str] = None) -> AsyncIterator[str]:
        async with self.AsyncSession() as session:
            try:
                stmt = select(SQLDocument.key)
                if prefix:
                    stmt = stmt.where(SQLDocument.key.like(f"{prefix}%"))
                result = await session.stream(stmt)
                async for row in result:
                    yield row[0]
            except Exception as e:
                logger.error(f"Error in ayield_keys: {e}")
                await session.rollback()

    def get_key_by_value(self, value: Dict) -> Optional[str]:
        source = value.get("metadata", {}).get("source", None)
        order = value.get("metadata", {}).get("order", None)
        if source is None or order is None:
            return None
        with self.SyncSession() as session:
            try:
                result = session.execute(
                    select(SQLDocument.key).where(
                        SQLDocument.value["metadata"]["source"].astext == source,
                        cast(SQLDocument.value["metadata"]["order"].astext, Integer)
                        == order,
                    )
                )
                key = result.scalar_one_or_none()
                return key
            except Exception as e:
                logger.error(f"Error in get_key_by_value: {e}")
                session.rollback()
                return None

    async def aget_key_by_value(self, value: Document) -> Optional[str]:
        source = value.metadata.get("source", None)
        order = value.metadata.get("order", None)
        if source is None or order is None:
            return None

        async with self.AsyncSession() as session:
            try:
                result = await session.execute(
                    select(SQLDocument.key).where(
                        SQLDocument.value["metadata"]["source"].astext == source,
                        cast(SQLDocument.value["metadata"]["order"].astext, Integer)
                        == order,
                    )
                )
                key = result.scalar_one_or_none()
                return key
            except Exception as e:
                logger.error(f"Error in get_key_by_value: {e}")
                await session.rollback()
                return None


async def test():

    from src.db.session import SyncSessionFactory, AsyncSessionFactory

    docstore = PostgresStore(
        sync_session_factory=SyncSessionFactory,
        async_session_factory=AsyncSessionFactory,
    )
    # async example
    keys = [key async for key in docstore.ayield_keys()]
    print(len(keys))
    if keys:
        docs = await docstore.amget([keys[0]])
        print(docs)
    # sync
    keys = [key for key in docstore.yield_keys()]
    print(len(keys))

if __name__ == "__main__":

    import asyncio
    asyncio.run(test())
