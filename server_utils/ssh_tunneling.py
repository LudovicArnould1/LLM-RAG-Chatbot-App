import os
import time

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder


def start_tunnel() -> None:
    """Start the SSH tunnel."""
    ssh_server_ip = os.getenv("SSH_SERVER_IP")
    username = os.getenv("SSH_USERNAME")
    password = os.getenv("SSH_PASSWORD")
    local_port = int(os.getenv("LOCAL_PORT", "8000"))
    server_port = int(os.getenv("SERVER_PORT", "8000"))

    tunnel = SSHTunnelForwarder(
        (ssh_server_ip, 22),
        ssh_username=username,
        ssh_password=password,
        remote_bind_address=("127.0.0.1", server_port),
        local_bind_address=("127.0.0.1", local_port),
    )
    tunnel.start()
    print(f"Tunnel established. Access the model at http://127.0.0.1:{local_port}")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        tunnel.stop()
        print("Tunnel closed.")

if __name__ == "__main__":
    # Load the environment variables from the .env file
    load_dotenv()
    start_tunnel()
