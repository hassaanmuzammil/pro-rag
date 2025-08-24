from typing import Literal
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Modifier,
    VectorParams,
    SparseVectorParams,
    MatchAny,
    MatchValue,
    Filter,
    FilterSelector,
    FieldCondition,
    Fusion,
    FusionQuery,
    Prefetch,
    SparseVector,
)

def normalize(vec):
    vec = np.array(vec)
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec


def create_collection(
    client: QdrantClient,
    collection_name: str,
    embedding_size: int,
    distance: Distance = Distance.COSINE,
    sparse_modifier: Modifier = Modifier.IDF,
) -> bool:
    """
    Create a Qdrant collection if it doesn't already exist.
    Returns:
        True if created, False if already exists.
    """
    if client.collection_exists(collection_name):
        return False

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=embedding_size,
                distance=distance,
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                modifier=sparse_modifier
            )
        },
    )
    return True

def search_collection(
    client: QdrantClient,
    collection_name: str,
    query: str,   
    model_dense = None,
    model_sparse = None,
    mode: Literal["sparse", "dense", "hybrid"] = "hybrid",
    filenames: str | list[str] = None,
    k: int = 5
) -> list[dict]:
    
    if not filenames:
        query_filter = None
    else:
        if isinstance(filenames, str):
            match = MatchValue(value=filenames)
        elif isinstance(filenames, list):
            match = MatchAny(any=filenames)

        query_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.source",
                    match=match
                )
            ]
        )

    # DENSE MODE
    if mode == "dense":
        dense_vector = model_dense.embed_query(query)
        dense_vector = normalize(dense_vector)

        result = client.query_points(
            collection_name=collection_name,
            query=dense_vector,
            with_payload=True,
            using="dense",
            limit=k,
            query_filter=query_filter
        )

    # SPARSE MODE
    elif mode == "sparse":
        sparse_vector = model_sparse.embed_query(query)

        result = client.query_points(
            collection_name=collection_name,
            query=SparseVector(
                indices=sparse_vector.indices,
                values=sparse_vector.values
            ),
            limit=k,
            with_payload=True,
            using="sparse",
            query_filter=query_filter
        )

    # HYBRID MODE
    elif mode == "hybrid":
        dense_vector = normalize(model_dense.embed_query(query))
        sparse_vector = model_sparse.embed_query(query)

        result = client.query_points(
            collection_name=collection_name,
            query=FusionQuery(fusion=Fusion.RRF),
            query_filter=query_filter,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=k
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_vector.indices,
                        values=sparse_vector.values
                    ),
                    using="sparse",
                    limit=k
                ),
            ],
            limit=k,
            with_payload=True
        )

    else:
        raise ValueError(f"Invalid mode: {mode}")

    return result

def delete_points_by_source(
    client: QdrantClient,
    collection_name: str,
    source: str,
) -> None:
    # Construct filter
    delete_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.source",
                match=MatchValue(value=source)
            )
        ]
    )

    # Delete points matching the filter
    client.delete(
        collection_name=collection_name,
        points_selector=FilterSelector(filter=delete_filter)
    )
