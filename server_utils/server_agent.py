import time
from pathlib import Path

import paramiko
from sshtunnel import SSHTunnelForwarder


class ServerConnection:
    """A class to handle SSH connections to a remote server."""

    def __init__(self, ip_address: str, username: str, password: str | None =
                 None, key_filename: str | None = None) -> None:
        """Initialize the ServerConnection class with the required connection details.

        :param ip_address: The IP address of the remote server.
        :param username: The SSH username.
        :param password: The SSH password (optional if key_filename is provided).
        :param key_filename: The path to the SSH private key file (optional if
        password is provided).
        """
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

    def connect(self) -> None:
        """Establish an SSH connection and open a shell on the server."""
        if self.password:
            self.client.connect(self.ip_address, username=self.username,
                                password=self.password, timeout=10)
        else:
            self.client.connect(self.ip_address, username=self.username,
                                key_filename=self.key_filename, timeout=10)
        self.shell = self.client.invoke_shell()
        self._wait_for_shell_ready()

    def _wait_for_shell_ready(self) -> None:
        """Wait until the shell is ready to receive commands."""
        while not self.shell.recv_ready():
            time.sleep(0.1)
        self.shell.recv(1000)  # Clear the buffer

    def execute_command(self, command: str) -> str:
        """Execute a command on the remote server and wait for it to complete.

        :param command: The command string to execute.
        :return: The output from the command execution.
        """
        self.shell.send(command + "\n")
        return self._wait_for_command_complete()

    def _wait_for_command_complete(self) -> str:
        """Wait for the command to complete and capture the output."""
        output = ""
        while True:
            if self.shell.recv_ready():
                output += self.shell.recv(5000).decode()
            if self._is_command_complete(output):
                break
            time.sleep(0.1)
        # Remove the command prompt from the output
        return output.replace(f"{self.username}@AlienwareRD:~$", "").strip()

    def _is_command_complete(self, output: str) -> bool:
        """Determine if the command has completed based on the output.

        :param output: Current output from the shell.
        :return: True if the command is complete, False otherwise.
        """
        return output.strip().endswith(f"{self.username}@AlienwareRD:~$")

    def close(self) -> None:
        """Close the SSH connection and the interactive shell."""
        if self.shell:
            self.shell.close()
        self.client.close()

    def start_tunnel(self, local_port : int = 8000,
                     server_port : int = 8000 ) -> None:
        """Start the SSH tunnel with default input/output ports 8000."""
        self.tunnel = SSHTunnelForwarder(
            (self.ip_address, 22),
            ssh_username=self.username,
            ssh_password=self.password,
            remote_bind_address=("127.0.0.1", server_port),
            local_bind_address=("127.0.0.1", local_port),
        )
        self.tunnel.start()
        print("Tunnel established. Access the model at http://127.0.0.1:8000")

        # Allow some time for the tunnel to establish
        time.sleep(2)

    def stop_tunnel(self) -> None:
        """Stop the SSH tunnel."""
        if self.tunnel:
            self.tunnel.stop()
            self.tunnel = None
            self.llm = None
            print("Tunnel closed.")


def load_credentials(file_path: str) -> dict[str, str]:
    """Load SSH credentials from a file.

    :param file_path: Path to the credentials file.
    :return: A dictionary with ip_address, username, and password.
    """
    credentials = {}
    with Path(file_path).open() as file:
        for line in file:
            key, value = line.strip().split("=")
            credentials[key] = value
    return credentials
