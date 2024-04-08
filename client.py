import socket


class IRCClient:
    """
    A simple IRC Client class for connecting to an IRC server, sending a ping,
    and disconnecting.
    """

    def __init__(self, host: str, port: int):
        """
        Initializes the IRC client with the server's host and port.

        :param host: The hostname or IP address of the IRC server.
        :param port: The port number of the IRC server.
        """
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> bool:
        """
        Attempts to connect to the IRC server.

        :return: True if the connection was successful, False otherwise.
        """
        try:
            self.socket.connect((self.host, self.port))
            print("Connected to IRC server.")
            return True
        except Exception as e:
            print(f"Failed to connect to IRC server: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Closes the connection to the IRC server.

        :return: True if the disconnection was successful, False otherwise.
        """
        try:
            self.socket.close()
            print("Disconnected from IRC server.")
            return True
        except Exception as e:
            print(f"Failed to disconnect from IRC server: {e}")
            return False

    def send_ping(self) -> bool:
        """
        Sends a PING command to the IRC server to check if it's responsive.

        :return: True if the PING was successfully sent and a response received, False otherwise.
        """
        try:
            self.socket.sendall(b"PING :ping\n")
            response = self.socket.recv(4096)
            print(f"Received: {response}")
            return True
        except Exception as e:
            print(f"Failed to send PING: {e}")
            return False
