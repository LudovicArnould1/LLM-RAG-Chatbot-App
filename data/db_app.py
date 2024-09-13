from __future__ import annotations

import sqlite3

import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Initialize ChromaDB client
db_name = "chroma_db_default_emb"
chroma_client = chromadb.PersistentClient("data/" + db_name)
db = chroma_client.get_collection(name=db_name)

search_kwargs = {"n_results": 5}

# Define FastAPI app
app = FastAPI()

class QueryRequest(BaseModel):
    """Represents a request for a query."""

    query: str
    n_docs: int = 5

class QueryResponse(BaseModel):
    """Represents the response for a query."""

    documents: list[str]
    context: str

class InsertQueryRequest(BaseModel):
    """Represents a request to insert a query."""

    query: str
    answer: str
    documents: list[str]


class FeedbackRequest(BaseModel):
    """Represents a request for feedback."""

    query: str
    feedback: str

@app.post("/similarity_search", response_model=QueryResponse)
def similarity_search(request: QueryRequest) -> QueryResponse:
    """Perform a similarity search in the ChromaDB vectorstore."""
    search_kwargs["n_results"] = request.n_docs
    query_results = db.query(query_texts=[request.query], **search_kwargs)

    if not query_results["documents"]:
        raise HTTPException(status_code=404, detail="No documents found.")

    documents = query_results["documents"][0]
    context = "\n\n\n".join(documents)
    return QueryResponse(documents=documents, context=context)


@app.post("/insert_query")
def insert_query(request: InsertQueryRequest) -> dict:
    """Insert a new query result into the queries.db file."""
    conn = sqlite3.connect("data/queries.db")
    cursor = conn.cursor()

    context = "\n\n\n".join(request.documents)

    cursor.execute("""
        INSERT INTO queries (query, answer, documents)
        VALUES (?, ?, ?)
    """, (request.query, request.answer, context))
    conn.commit()
    conn.close()

    return {"message": "Query inserted successfully"}

@app.post("/write_feedback")
def write_feedback(request: FeedbackRequest) -> dict:
    """Write feedback into the queries.db file."""
    # Store the feedback in the database
    conn = sqlite3.connect("data/queries.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE queries
        SET feedback = ?
        WHERE query = ?
    """, (request.feedback, request.query))
    conn.commit()
    conn.close()

    return {"message": "Feedback received"}

# Additional route to ensure the server is running
@app.get("/")
def read_root() -> dict:
    """Check if server is running."""
    return {"message": "Server is running"}
