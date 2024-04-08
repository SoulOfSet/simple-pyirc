import socket


class IRCClient:
    """
    A simple IRC Client class for connecting to an IRC server, sending a ping,
    and disconnecting.
    """

    def __init__(self, host: str, port: int, userinfo: str):
        self.host = host
        self.port = port
        self.nickname = None
        self.userinfo = userinfo
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect(self) -> bool:
        """
        Attempts to connect to the IRC server.

        :return: True if the connection was successful, False otherwise.
        """
        try:
            self.socket.connect((self.host, self.port))
            print("Connected to IRC server.")
            self.connected = True
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
            self.connected = False
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

    def register(self, nickname: str) -> bool:
        """
        Registers the user with the IRC server using a specified nickname and predefined user information.

        :param nickname: The nickname to register with the IRC server.
        :return: True if the registration was successful, False otherwise.
        """
        if not self.connected:
            print("You must connect before registering.")
            return False
        self.nickname = nickname
        try:
            self.socket.sendall(f"NICK {self.nickname}\n".encode())
            self.socket.sendall(f"USER {self.nickname} 0 * :{self.userinfo}\n".encode())
            # Wait for a response from the server
            response = self.socket.recv(4096).decode()
            print(f"Registration response: {response}")
            return True
        except Exception as e:
            print(f"Failed to register with IRC server: {e}")
            return False

    def set_nickname(self, new_nickname: str) -> bool:
        """
        Updates the user's nickname on the IRC server to a new value.

        :param new_nickname: The new nickname to set for the user.
        :return: True if the nickname was successfully updated, False otherwise.

        """
        try:
            self.socket.sendall(f"NICK {new_nickname}\n".encode())
            # Wait for a response from the server
            response = self.socket.recv(4096).decode()
            if "Nickname is already in use" in response:
                print("Nickname collision, please choose another.")
                return False
            else:
                self.nickname = new_nickname
                print(f"Nickname updated to {new_nickname}")
                return True
        except Exception as e:
            print(f"Failed to update nickname: {e}")
            return False

