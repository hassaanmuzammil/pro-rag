import os
import uuid
import shutil
import tempfile
from fastapi import Query, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.builder import mc, qdrant_client, pipeline
from src.qdrant import delete_points_by_source
from src.db.session import get_async_session
from src.db.models import UploadedFile
from src.logger import logger
from src.config import (
    MINIO_BUCKET, 
    ALLOWED_EXTENSIONS, 
    QDRANT_COLLECTION,
)

router = APIRouter()

@router.get("/")
async def get_files(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(UploadedFile)
        .limit(limit)
        .offset(offset)
    )
    files = result.scalars().all()
    return {
        "limit": limit,
        "offset": offset,
        "files": files
    }

@router.get("/{filename}")
async def get_file_by_name(filename: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.filename == filename)
    )
    file = result.scalars().first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(filename: str, session: AsyncSession = Depends(get_async_session)):

    result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.filename == filename)
    )
    file = result.scalars().first()
    
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Delete from vectordb
    try:
        source = file.meta.get("vectordb_metadata_source") if file.meta else None
        delete_points_by_source(
            client=qdrant_client,
            collection_name=QDRANT_COLLECTION,
            source=source,
        )
    except Exception as e:
        logger.error(f"Failed to delete points using source {source} Caused by: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    # Delete from uploaded files metadata
    await session.execute(
        delete(UploadedFile).where(UploadedFile.filename == filename)
    )
    
    # Delete from docstore
    await session.execute(
        text("DELETE FROM docstore WHERE value->'metadata'->>'source' = :source"),
        {"source": source}
    )
    await session.commit()
    
    return

@router.post("/upload")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)    
):
    filename = file.filename
    
    # Validate extension
    ext = os.path.splitext(filename)[1].lower() 
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check if file exists
    result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.filename == filename)
    )
    existing_file = result.scalars().first()
    if existing_file:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A file with this name already exists. Please delete it before uploading a new version."
        )
        
    # Prepend UUID to the filename
    prefix = ""
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    object_name = prefix + unique_filename
    
    # Set temporary directory
    temp_dir = "/tmp"
    temp_file_path = os.path.join(temp_dir, filename)
    
    try:
        # Upload file.file (BinaryIO stream) directly
        mc.upload_file( 
            bucket_name=MINIO_BUCKET,
            data=file.file,
            object_name=object_name
        )
    except Exception as e:
        logger.error(f"Upload to MinIO failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    try:
        # Download file to temp dir
        mc.download_file(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            file_path=temp_file_path
        )
        # Load file from local path as langchain documents
        documents = pipeline.load(temp_file_path)
        os.remove(temp_file_path)
        
        # Index documents in vectorstore
        await pipeline.index(documents=documents)
    
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    try:
        # Update uploaded files metadata
        metadata = {
            "blob_storage_path": object_name,
            "vectordb_metadata_source": temp_file_path,
        }
        file_entry = UploadedFile(
            filename=filename,
            meta=metadata
        )
        session.add(file_entry)
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to save file metadata: {e}.")
        
        # Clean up
        # Delete from vectorstore
        delete_points_by_source(
            client=qdrant_client,
            collection_name=QDRANT_COLLECTION,
            source=temp_file_path,
        )
        
        # Delete from docstore
        await session.execute(
            text("DELETE FROM docstore WHERE value->'metadata'->>'source' = :source"),
            {"source": temp_file_path}
        )
        await session.commit()
        
        raise HTTPException(status_code=500, detail="Internal Server Error")
      
    return JSONResponse(
        content={
            "original_filename": filename,
            "blob_storage_path": object_name,
            "vectordb_metadata_source": temp_file_path,
            "message": "File uploaded and indexed successfully!"
        }
    )
