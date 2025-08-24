import uvicorn
from fastapi import FastAPI

from src.config import PORT
from src.api.file import router as file_router

app = FastAPI(
    title="API Server",
    version="1.0.0",
    description="API Server",
)

app.include_router(file_router, prefix="/files", tags={"Files"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)