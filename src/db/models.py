import uuid
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, func, ForeignKey 
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = "file"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(Text, unique=True, nullable=False)
    meta = Column(JSONB, nullable=False) # name 'metadata' is reserved 
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)    

class SQLDocument(Base):
    __tablename__ = "docstore"
    
    key = Column(String, primary_key=True)
    value = Column(JSONB)
    
    def repr(self):
        return f"<SQLDocument(key='{self.key}', value='{self.value}')>" 

class DocumentModel(BaseModel):
    key: Optional[str] = Field(None)
    page_content: Optional[str] = Field(None)
    metadata: dict = Field(default_factory=dict)

# Define model for Thread
class Thread(Base):
    __tablename__ = "thread"
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    thread_name = Column(String, nullable=True, default="")
    user_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    last_modified_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Define relationship
    messages = relationship("Message", back_populates="thread")

# Define model for Chat
class Message(Base):
    __tablename__ = "message"
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("thread.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    message = Column(String, nullable=False)
    response = Column(String, nullable=True)
    intermediate_steps = Column(JSONB, nullable=True)
    feedback = Column(Boolean, nullable=True)
    feedback_comment = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    last_modified_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Define relationships
    thread = relationship("Thread", back_populates="messages")
