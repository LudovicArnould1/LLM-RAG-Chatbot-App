import os
import time

import chromadb
from dotenv import load_dotenv
from env.langchain_env import EnvironmentConfig
from fastapi import FastAPI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

from server_utils.ollama_client import OllamaClientLangchain
from server_utils.server_agent import ServerConnection

# Setup environment
EnvironmentConfig.setup_environment()
load_dotenv()

# Server config and connexion
server_credentials = {"username": os.getenv("USERNAME"),
                       "password": os.getenv("PASSWORD"),
                       "ip_address": os.getenv("SERVER_IP")}

ollama_config = {"ollama_host" : os.getenv("OLLAMA_HOST"),
                      "model" : "llama3:latest", "temperature" : 0, "kwargs":{}}

# Server connection instance
server_connexion = ServerConnection(**server_credentials)

# Load chroma db
db_name = "chroma_db_default_emb"
chroma_client = chromadb.PersistentClient( "data/" +db_name)
db = chroma_client.get_collection(name= db_name)

search_kwargs = {"n_results": 5}

# LLM
model_name = "llama3:latest"

agent_llm = OllamaClientLangchain(connection=server_connexion,
                                    ollama_host=ollama_config["ollama_host"])
llm = agent_llm.load_model(model=model_name)



# Try to charge the model with remote llm

prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You
    are a training recommendation assistant. Use the retrieved documents to
    answer the query. \n
    If queried for a non-specific number, return a structured answer with at
    most 3 formations. \n
    In your answer, each formation should be separated from the others by numbers I. II. III. ...\n
    For each formation, indicate only the following elements and nothing else :
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

user_query = "Recommend 3 SQL courses"
start_time = time.time()
query_results = db.query(query_texts=[user_query], **search_kwargs)
end_time = time.time()
print(f"Time to access database: {end_time - start_time}")

documents = query_results["documents"][0]
# concatenate documents with separation between them
documents = "\n\n\n".join(documents)

generation = chain.invoke({"query": user_query, "documents": documents})

print(f"Query: {user_query}")
print(f"Answer: {generation}")

agent_llm.end_connection()


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


