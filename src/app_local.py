import time

import chromadb
from fastapi import FastAPI
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from env.langchain_env import EnvironmentConfig

# Setup environment
EnvironmentConfig.setup_environment()

# Load chroma db
chroma_client = chromadb.PersistentClient(path="data/chroma_db_default_emb")

db = chroma_client.get_collection(name="chroma_db_default_emb")

search_kwargs = {"n_results": 5}

# LLM
local_llm = "qwen2:7b"
llm = ChatOllama(model=local_llm, temperature=0)

# Try to charge the model with remote llm

prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You
    are a training recommendation assistant. Use the retrieved documents to
    answer the query. \n
    If queried for a non-specific number, return at most 3 formations. \n
    For each formation, indicate the following elements and nothing else :
    Title: formation title \n
    Description: brief summary (3 sentences at most) of the formation \n
    Provider : formation provider (if written, otherwise "unknown")\n
    Price: formation price (if any, otherwise "free")\n
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Question: {query} \n
    Context: {documents}
    Answer: Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["query", "documents"],
)

chain = prompt | llm | StrOutputParser()


# Define FastAPI app
app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    documents: list[str]

@app.post("/query", response_model=QueryResponse)
def query_llm(request: QueryRequest):
    # Load the query embeddings

    user_query = request.query
    start_time = time.time()
    query_results = db.query(query_texts=[user_query], **search_kwargs)
    end_time = time.time()
    print(f"Time to access database: {end_time - start_time}")

    documents = query_results["documents"][0]

    generation = chain.invoke({"query": request.query, "documents": documents})

    print(f"Query: {request.query}")
    print(f"Answer: {generation}")

    # Prints first two docs
    print(f"Documents: {documents[0]}")
    print(f"\n\n\n Documents: {documents[1]}")

    return QueryResponse(answer=generation, documents=documents)


