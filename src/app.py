from __future__ import annotations

import os
from http.client import HTTPException

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel

load_dotenv()

# Retrieve the DB from the configuration
DB_URL = os.getenv("DB_URL", "http://localhost:8000")
SEARCH_URL = DB_URL + "/similarity_search"
FEEDBACK_URL = DB_URL + "/write_feedback"
WRITE_URL = DB_URL + "/insert_query"


# LLM
model_name = "llama-3.1-70b-versatile"  #"gemma-7b-it"

# Chatbot design : Prompt
prompt = ChatPromptTemplate.from_template(
    """Answer any question the user may have based on the following context:
<context>
{context}
</context>

Question: {input}""",
)

# Define FastAPI app
app = FastAPI()

class QueryRequest(BaseModel):
    """Represent a query request."""

    query: str

class QueryResponse(BaseModel):
    """Represent a query response."""

    answer: str
    documents: list[str]

class FeedbackRequest(BaseModel):
    """Represent a feedback request."""

    query: str
    feedback: str


@app.post("/query", response_model=QueryResponse)
def query_llm(request: QueryRequest, model_name : str = model_name,
              n_docs: int = 3) -> QueryResponse:
    """Query the LLM model with the given request and return the response.

    Args:
    ----
        request (QueryRequest): The query request.
        model_name (str): The name of the LLM model.
        n_docs (int): The number of documents to retrieve.

    Returns:
    -------
        QueryResponse: The query response containing the answer and documents.

    """
    # Make a request to the similarity_search endpoint
    response = requests.post(
        SEARCH_URL,
        json={"query": request.query, "n_docs": n_docs},
        timeout=20,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="""Failed
                            to perform similarity search.""")

    similarity_search_result = response.json()
    documents = similarity_search_result["documents"]
    context = similarity_search_result["context"]

    # Chatbot design : Document retrieval (out of chain) + prompt + model
    chat = ChatGroq(model=model_name)
    chain = prompt | chat

    generation = chain.invoke({"input": request.query, "context": context})

    # Make a request to the insert_query endpoint
    insert_response = requests.post(
        WRITE_URL,
        json={"query": request.query, "answer": generation.content,
              "documents": documents},
        timeout=5,
    )

    if insert_response.status_code != 200:
        raise HTTPException(status_code=insert_response.status_code,
                            detail="Failed to insert query result.")

    return QueryResponse(answer=generation.content, documents=documents)

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest) -> dict:
    """Submit feedback for a query.

    Args:
    ----
        request (FeedbackRequest): The feedback request.

    Returns:
    -------
        dict: A dictionary indicating the success of the feedback submission.

    """
    # Make a request to the write_feedback endpoint
    response = requests.post(
        FEEDBACK_URL,
        json={"query": request.query, "feedback": request.feedback},
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                            detail="Failed to submit feedback.")

    return {"message": "Feedback received"}
