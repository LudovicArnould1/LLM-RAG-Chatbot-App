# Adaptive Learning with AI

This project simply connects an LLM to a database (RAG), builds a simple user-friendly interface and deploys the whole thing to Azure using Docker containers. Basic knowledge of python is required.

The initial work, from which it is extracted, consisted in building a prototype for an adaptive training app powered by an LLM and RAG. A few unchecked modifications (it was first developed on gitlab) could cause a few bugs to occur, especially regarding how to handle env variables and deployment (ci/cd, docker config, azure config).

Depending on your use-case, many improvements can be considered. In particular, security regarding how to handle env variables is totally neglected. The RAG process is excessively simple and could be greatly improved using other LLM agents following [langchain-agent-tutorial](https://github.com/langchain-ai/langgraph/blob/main/examples/rag/langgraph_rag_agent_llama3_local.ipynb) for instance.

## Table of Contents
1. [Tutorial - exploration](#tutorial-exploration)
2. [Technical stack](#Technical-stack)
3. [Information about the structure](#information-about-the-structure)
4. [Installation and Setup](#installation-and-setup)
5. [Trying the app](#trying-the-app)
6. [Contact Information](#contact-information)

<details>
<summary><h2>Tutorial (Exploration of the repo)</h2></summary>

To build such an app, a few key ingredients are required. We will go through each of them, explaining a bit about them and how they are developed in this repo.
After a small overview, we will have a look at the global configs (git, azure, docker, fastapi), the LLM setup, the database configuration and the frontend.

<details>
<summary><h4>Overview</h4></summary>

- **Backend** (src dir): An LLM is connected to a doc database. Each user query triggers a similarity search within the database to find the most relevant documents. The query and documents are then sent to an LLM (LLaMA 3.1 70B) which answers to the user based on the docs' content.
- **Database** (data dir): The database is a ChromaDB vectorstore that is queried by the backend. Another database keeps track of the queries, outputs, and documents.
- **Frontend**(frontend dir): A basic Streamlit frontend where the user can write the query that will be sent to the backend. The output is then displayed, and a dropdown menu shows the documents that were used to provide the answer. There is also a feedback feature.

</details>

<details>
<summary><h4>Global setup</h4></summary>

From writing a single python program that we can run from our console to building a webapp accessible from another computer, a whole world of possibilities opens before us. Many among all the choices I have made to build this app are arbitrary. I'll try my best to explain why a specific tool/library is chosen at each step, although the answer is generally "because it was the most popular or the first I could find".

As I see it, the two main levels of development are local (our computer) and deployed (accessible with a web url). One of the big challenges of developement is reaching the deployed state in a clean way, i.e. with a behavior that is similar to the local behavior of your app. An amazing tool to accomplish this fate is Docker. We can put our app into a docker *container*, a kind of intermediary deployment state that ensures an agnostic behavior, that is, independent from the local or remote config. We will go through each of these development steps, local, container (docker), and deployed.

<details>
<summary><h5>Local development</h5></summary>

Developing locally is simple. You can test your program directly in the console and you can define all your env variables (git token, openai token, azure password, etc) inside your code. However, these practices do not meet future deployment constraints. So let's have a look at a few useful tools and practices.

**FastAPI** : FastAPI (used in the src/app.py files) is used to build the backend of our app. It it a very handy tool which can turn our python functions into callable "apps" or "programs". The next code snippet from src/app.py shows a simple use:

```
from fastapi import FastAPI
from pydantic import BaseModel

# Define FastAPI app
app = FastAPI()

class QueryResponse(BaseModel):
    """Represent a query response."""

    answer: str
    documents: list[str]


@app.post("/query", response_model=QueryResponse)
def query_llm(request: QueryRequest,n_docs: int = 6):
# ...
```
The key elements are the app declaration and the decorator. The QueryResponse class using BaseModel from Pydantic is disposable; its main purpose is to assess that the input parameters of our functions are properly set (type, format, etc). The app and decorator make the function callable from an external file, for instance via an url link. With this regard, we can try it as follows:
- Start the app in the console using `uvicorn src.app:app --host 0.0.0.0 --port 8000` 
- Access the app from a webpage at `https://localhost:8000`
As the name "localhost" suggests, this app is simply accessible from our computer. We will see later how to deploy it, but before that we can still connect it to the frontend.

**Streamlit**: Our frontend is based on one of the simplest frontend library I could find to build frontends in Python. It is not very flexible but quite easy to use and very friendly for basic apps. It can be run as follows:
- `streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0`

Obviously, the frontend should be connected to the backend. Therefore we have to tell the frontend to look for the backend url (here 0.0.0.0:8000) when sending requests. In our case, we have two requests:
- `/query` to send a query to the backend, and then we retrieve the generation content and the documents used for the query
- `/feedback` to send feedback about a query/answer.

Locally, we can simply write the url adress of the backend in the frontend file `frontend/streamlit_app.py` to access the app. However, this will not work on the deployed app, because the url will be different. Therefore, we need to set up the frontend to dynamically find the url of the deployed app. This is done using env variables.

</details>

<details>
<summary><h5>Env variables</h5></summary>

Env variables are used to store information that may vary across environments (local, container, deployed). Locally, we can simply write them in a .env file. For instance, it can contain the url of the backend, an openai token_access_key, etc. Then, we can also store them in git in order to make the deployment automatic. For instance, in our .github/workflows file that sets up an automatic deployment to azure, we need to access our azure credentials.

Finally, we can also store variables directly in the deployed app using the Azure portal or Azure CLI (command line interface). If you take a look at the `config.py` file, you can see that we first retrieve the env variable `ENV` which indicates the environment. Then, based on this, we retrieve the corresponding backend url. `ENV` is set in .env locally, in the docker file and in the azure app settings.

</details>

<details>
<summary><h5>Docker</h5></summary>

The Docker files are quite straightforward. They specify the ports to expose, the command to run to start the app, the volumes to mount, the env variables (eventually). They are used to build the docker images. Once built using `docker build`, we can run them using `docker run` and access the app from the corresponding port (localhost:8000, localhost:8501, etc). We can also push them to a docker registry like Azure Container Registry (ACR) to deploy them to our app using `docker push`.

</details>

<details>
<summary><h5>Azure</h5></summary>

On Azure, we can create a Web App service to host our app. Then we need to link it to our docker image. This is done using a so-called "container registry" which is nothing more than a docker registry (ACR) accessible from Azure. Once we have linked our web app to our docker registry, Azure will automatically deploy our app when we push a new image to the registry.

</details>

</details>

<details>
<summary><h4>Data</h4></summary>

In this repo, I only selected a few toy documents from Wikipedia to create the vector database. This is done in the `data/vector_db.py` file. The vector database contains the embeddings of all the documents. It is based on Chroma which performs fast similarity searches. Here the data is accessible via an app as well. If deployed, you can access it with the corresponding url, otherwise you can run it locally using `uvicorn data.data_preprocessing:app --host 0.0.0.0 --port 8001` and then specify the url localhost:8001 in the backend (`DB_URL`, at the beginning of the `src/app.py` file).

</details>

<details>
<summary><h4>The backend</h4></summary>

It contains a few classes to handle the requests and responses of the app. The main class is the `QueryRequest` class that is used to send a query to the backend. It contains the query and the number of documents to retrieve. The `QueryResponse` class is used to retrieve the answer and the documents used to answer the query. The `query_llm` function is used to send a query to the backend and retrieve the answer and the documents used to answer the query. LLaMA3.1 70B is used as the LLM by default, provided by Groq with an api key.

</details>

<details>
<summary><h4>ci-cd</h4></summary>

The ci-cd pipeline is defined in the `.github/workflows/ci-cd.yml` file. It is a github action that is triggered on a push to the repository. It contains several jobs to lint the code, run some tests and deploy the app to Azure automatically. Therefore it requires a few secrets to be set in the github repository settings (ACR login server, ACR username, ACR password, etc).

</details>

<details>
<summary><h4>Server Utils</h4></summary>

This dir contains a few scripts to run the computations on a local server with the Ollama service, using Langchain or not.

</details>

</details>

<details>
<summary><h2>Technical stack</h2></summary>

- **LLM**: Currently using Groq service, providing fast inference for several open-source models. LLaMA 3.1 70B is used by default, and a smaller model is used for test purposes. Langsmith is also used to retrieve metrics about the LLM.
- **FastAPI**: Used to turn Python functions into callable apps.
- **Course database**: Stored within a ChromaDB vectorstore for faster similarity search. The database uses Chroma default embeddings (dim 384).
- **App deployment**: Three web apps (database, backend, frontend) are hosted on Azure as Web App services. The apps are linked to three Docker images that are stored within an Azure Container Registry (ACR).
- **Testing**: Basic functional tests are (to be) set up to assess the app's behavior before deployment (CI/CD pipeline defined in `.git-ci.yml`).

</details>

<details>
<summary><h2>Information about the structure</h2></summary>

- The backend is located in the `src` directory, the frontend in the `frontend` directory. In the `src` directory, the `app.py` file is used for deployment.
- The `server_utils` directory can be used to run the computations on a local server with the Ollama service.
- The `data` directory stores all the files related to data processing/querying.
- A config file sets up the ENV variable ("local", "docker" or "azure") and loads variables from the `.env` file.

</details>

<details>
<summary><h2>Installation and Setup</h2></summary>

**Prerequisites**
- Python 3.12
- Docker
- Azure CLI (for deployment)

Environment variables (In particular, an URL to access a database)

</details>

<details>
<summary><h2>Trying the app</h2></summary>

You can try the original app, a prototype for a training course recommendation agent, here: [app](https://alwai-front.azurewebsites.net/)

You can run the git locally after cloning it, installing requirements and configurating the env variables (It currently needs a Groq api token and a Langsmith api token).

- **Data**: `uvicorn data.data_preprocessing:app --host 0.0.0.0 --port 8001`
This is used to access the data from the backend (and frontend).

- **Backend**: `uvicorn src.app:app --host 0.0.0.0 --port 8000`
The backend should now be running on http://localhost:8000.


- **Frontend**: `streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0`
The frontend should now be running on http://localhost:8501.

</details>

<details>
<summary><h2>Contact information</h2></summary>

Feel free to reach out for anything (on LinkedIn or by mail).