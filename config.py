import os

from dotenv import load_dotenv


class Config:
    """Configuration class for the application."""

    # Load environment variables from .env file if present
    load_dotenv()
    ENV = os.getenv("ENV", "local")

    @staticmethod
    def get_backend_url() -> str:
        """Get the API URL based on the environment.

        Returns
        -------
            str: The Backend URL.

        """
        if Config.ENV == "local":
            return "http://localhost:8000"
        if Config.ENV == "docker":
            return "http://fastapi:8000"
        if Config.ENV == "azure":
            return os.getenv("BACKEND_URL", os.getenv("BACKEND_URL"))

        else:  # noqa: RET505
            msg = f"Unknown environment: {Config.ENV}"
            raise ValueError(msg)
