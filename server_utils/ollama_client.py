from langchain_community.chat_models import ChatOllama

from server_utils.server_agent import ServerConnection, load_credentials


class OllamaClient:
    """Handle interactions with Ollama instances on the remote server."""

    def __init__(self, connection: ServerConnection, ollama_host: str) -> None:
        """Initialize the OllamaClient class.

        :param connection: An instance of the ServerConnection class.
        :param ollama_host: The hostname of the Ollama instance on the server.
        """
        self.connection = connection
        self.ollama_prefix = f"OLLAMA_HOST={ollama_host}"

    def load_model(self, model: str) -> None:
        """Load the LLM on the remote server.

        :param model: Name of the LLM to load. Should already be downloaded
        on the server.
        """
        # Check if model is in the database
        get_list_cmd = f"{self.ollama_prefix} ollama list"
        ollama_list = self.connection.execute_command(get_list_cmd)
        print("List of available models:\n", ollama_list)

        if model not in ollama_list:
            msg = f"""Model {model} not found on the server. Download it first
            using 'ollama pull' after checking server memory."""
            raise ValueError(msg)

        load_model_cmd = f"{self.ollama_prefix} ollama pull {model}"
        output = self.connection.execute_command(load_model_cmd)
        print(output)

    def query(self, model: str, query: str) -> str:
        """Query the loaded LLM on the remote server.

        :param model: The name of the language model to query.
        :param query: The query string to send to the language model.
        :return: The output from the LLM.
        """
        command = f'{self.ollama_prefix} ollama run {model} "{query}"'
        return self.connection.execute_command(command)


class OllamaClientLangchain:
    """Handle interactions with Ollama instances on the remote server."""

    def __init__(self, connection: ServerConnection, ollama_host: str):
        self.connection = connection
        self.ollama_prefix = f"OLLAMA_HOST={ollama_host}"

    def load_model(self, model: str):
        # Check if model is in the database
        get_list_cmd = f"{self.ollama_prefix} ollama list"
        self.connection.connect()
        ollama_list = self.connection.execute_command(get_list_cmd)
        print("List of available models:\n", ollama_list)
        self.connection.close()

        if model not in ollama_list:
            msg = f"""Model {model} not found on the server. Download it first
            using 'ollama pull' after checking server memory."""
            raise ValueError(msg)

        self.connection.start_tunnel()
        base_url = "http://127.0.0.1:8000"

        self.llm = ChatOllama(model=model, base_url=base_url)

        return self.llm

    def end_connection(self):
        self.connection.stop_tunnel()
        self.llm = None


if __name__ == "__main__":

    # Load credentials from file
    path_to_loading_credentials = "env/server_env.txt"
    credentials = load_credentials(path_to_loading_credentials)
    server_credentials = {key: credentials[key] for key in list(credentials)[:3]}

    ollama_config = {"ollama_host" : credentials["ollama_host"],
                        "model" : "qwen2:7b", "temperature" : 0, "kwargs":{}}

    # Server connection instance
    server_connection = ServerConnection(**server_credentials)
    server_connection.connect()

    # Ollama client instance
    ollama_client = OllamaClient(connection=server_connection,
                                ollama_host=ollama_config["ollama_host"])
    ollama_client.load_model(model=ollama_config["model"])

    # Query the LLM
    response1 = ollama_client.query(model="qwen2:7b", query="Say something")
    print(response1)

    # Close connection
    server_connection.close()

    # test ollamaclientLangchain class
    agent_llm = OllamaClientLangchain(connection=server_connection,
                                        ollama_host=ollama_config["ollama_host"])
    llm = agent_llm.load_model(model=ollama_config["model"])

    llm.invoke("Hello, how are you?")

    agent_llm.end_connection()
