# Production-ready RAG Application

## Detailed Design

[Detailed Design](https://deepwiki.com/hassaanmuzammil/pro-rag)

This project implements a **Retrieval-Augmented Generation (RAG)** application with a fully production-ready stack.

## 🚀 Tools & Technologies

- **Postgres** – relational database for structured storage  
- **MinIO** – S3-compatible object storage for files
- **Qdrant** – high-performance vector database for semantic search  
- **FastAPI** – backend API for RAG pipelines and orchestration  
- **Chainlit** – interactive frontend for chat-based interaction with the RAG system  
- **OpenAI** – large language model (LLM) provider for inference  

## Environment Setup

```sh
uv pip install -e .
```

## Run BE
```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Run Chainlit UI
```sh
cd frontend
PYTHONPATH=.. chainlit run app.py --host 0.0.0.0 --port 8888
```
