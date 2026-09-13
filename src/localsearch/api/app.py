from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from localsearch.database.connection import DatabaseManager
from localsearch.indexing.indexer import index_directory
from localsearch.retrieval.bm25 import lexical_search
from localsearch.retrieval.hybrid import hybrid_search
from localsearch.retrieval.semantic import semantic_search


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    mode: Literal["lexical", "semantic", "hybrid"] = "hybrid"
    file_type: str | None = None
    path: str | None = None
    rerank: bool = True


class IndexRequest(BaseModel):
    paths: list[str] = Field(min_length=1)


def create_app(db_path: str | Path = "localsearch.db") -> FastAPI:
    database_path = str(Path(db_path).expanduser())
    app = FastAPI(title="LocalAI Search", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        DatabaseManager(database_path)
        return {"status": "ok"}

    @app.get("/stats")
    def stats() -> dict[str, int | str]:
        database = DatabaseManager(database_path)
        files = database.list_files()
        return {
            "files": len(files),
            "chunks": database.get_chunk_count(),
            "database": database_path,
        }

    @app.post("/search")
    def search(request: SearchRequest) -> dict:
        common = {
            "db_path": database_path,
            "limit": request.limit,
            "file_type": request.file_type,
            "path_filter": request.path,
        }
        if request.mode == "lexical":
            results = lexical_search(request.query, **common)
        elif request.mode == "semantic":
            results = semantic_search(request.query, **common)
        else:
            results = hybrid_search(request.query, **common, rerank=request.rerank)
        return {"query": request.query, "mode": request.mode, "results": results}

    @app.post("/index")
    def index(request: IndexRequest) -> dict[str, object]:
        summary = index_directory(request.paths, db_path=database_path)
        return {"status": "completed", "summary": summary}

    @app.get("/files/{file_id}")
    def file_detail(file_id: int) -> dict:
        database = DatabaseManager(database_path)
        file_record = database.get_file_by_id(file_id)
        if file_record is None:
            raise HTTPException(status_code=404, detail="File not found")
        return file_record

    return app


app = create_app()
