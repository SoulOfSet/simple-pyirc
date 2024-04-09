import re
import socket
import threading
from time import sleep


class IRCClient:
    """
    A simple IRC Client clss for connecting to an IRC server, sending a ping,
    and disconnecting.
    """

    def __init__(self, host: str, port: int, userinfo: str):
        self.listening_thread = None
        self.host = host
        self.port = port
        self.nickname = None
        self.userinfo = userinfo
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.channels = set()
        self.channel_users = {}

    def connect(self) -> bool:
        """
        Attempts to connect to the IRC server.

        :return: True if the connection was successful, False otherwise.
        """
        try:
            self.socket.connect((self.host, self.port))
            print("Connected to IRC server.")
            self.connected = True
            self.start_listening()
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
            sleep(1)
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

    def join_channel(self, channel: str) -> bool:
        """
        Joins a specific channel.

        :param channel: The channel name to join.
        :return: True if the channel join attempt was made, False otherwise.
        """
        if not self.connected:
            print("You must be connected to join a channel.")
            return False
        try:
            self.socket.sendall(f"JOIN {channel}\n".encode())
            self.channels.add(channel)  # Add to the internal set of channels
            print(f"Attempted to join channel: {channel}")
            return True
        except Exception as e:
            print(f"Failed to join channel {channel}: {e}")
            return False

    def leave_channel(self, channel: str) -> bool:
        """
        Leaves a specific channel.

        :param channel: The channel name to leave.
        :return: True if the channel leave attempt was made, False otherwise.
        """
        if not self.connected:
            print("You must be connected to leave a channel.")
            return False
        try:
            self.socket.sendall(f"PART {channel}\n".encode())
            self.channels.discard(channel)  # Remove from the internal set of channels
            print(f"Attempted to leave channel: {channel}")
            return True
        except Exception as e:
            print(f"Failed to leave channel {channel}: {e}")
            return False

    def start_listening(self):
        """
        Starts a new thread that listens for messages from the server.
        """
        self.listening_thread = threading.Thread(target=self.listen_to_server, daemon=True)
        self.listening_thread.start()

    def listen_to_server(self):
        """
        The target function for the listening thread. It continuously listens for messages from the server
        and handles them using `handle_server_response`.
        """
        while self.connected:
            try:
                response = self.socket.recv(4096).decode('utf-8', 'ignore').strip()
                if response:
                    print(f"Server says: {response}")
                    self.handle_server_response(response)
            except Exception as e:
                print(f"Error listening to server: {e}")
                self.connected = False
                raise e

    def handle_server_response(self, response):
        """
        Handles responses from the server by dispatching them to specific handler functions based on
        the response type (e.g., PING, PRIVMSG).

        :param response: The raw response string from the server.
        """
        if response.startswith("PING"):
            self.socket.sendall((response.replace("PING", "PONG") + "\n").encode())
        elif "PRIVMSG" in response:
            self.handle_privmsg(response)
        elif "JOIN" in response:
            self.handle_join(response)
        elif "PART" in response:
            self.handle_part(response)
        elif "353" in response:
            self.handle_names(response)

    def handle_privmsg(self, response):
        """
        Handles a PRIVMSG (Private Message) from the server. This method extracts the sender's nickname,
        the target (which can be a channel or a user), and the message content, then prints the message.

        The PRIVMSG command is used in IRC to send private messages between users or to send messages to channels.

        :param response: The raw response string from the server containing the PRIVMSG command.
        """
        sender = re.search(r":(\S+)!", response).group(1)
        channel_or_user = re.search(r"PRIVMSG (\S+)", response).group(1)
        message = re.search(r"PRIVMSG \S+ :(.+)", response).group(1)
        print(f"Message from {sender} in {channel_or_user}: {message}")

    def handle_join(self, response):
        """
        Handles a JOIN message from the server. This method extracts the user who joined and the channel
        they joined, then updates the internal mapping of users to channels and prints a message indicating
        the user has joined the channel.

        The JOIN command is used in IRC for a user to start listening to the traffic from a specified channel.

        :param response: The raw response string from the server containing the JOIN command.
        """
        user = re.search(r":(\S+)!", response).group(1)
        channel = re.search(r"JOIN (\S+)", response).group(1)
        if user not in self.channel_users:
            self.channel_users[user] = set()
        self.channel_users[user].add(channel)
        print(f"{user} has joined {channel}")

    def handle_part(self, response):
        """
        Handles a PART message from the server. This method extracts the user who left and the channel
        they left, then updates the internal mapping of users to channels and prints a message indicating
        the user has left the channel.

        The PART command is used in IRC for a user to leave a channel.

        :param response: The raw response string from the server containing the PART command.
        """
        user = re.search(r":(\S+)!", response).group(1)
        channel = re.search(r"PART (\S+)", response).group(1)
        if user in self.channel_users and channel in self.channel_users[user]:
            self.channel_users[user].remove(channel)
        print(f"{user} has left {channel}")

    def handle_names(self, response):
        """
        Handles the NAMES response from the server. This method extracts the channel name and the list of
        nicknames in that channel, then updates the internal mapping of channels to users and prints the
        list of users in the channel.

        The NAMES command is used in IRC to list all visible nicknames that are part of a specified channel.

        :param response: The raw response string from the server containing the NAMES list.
        """
        channel = re.search(r"= (\S+)", response).group(1)
        names = re.search(r":(.+)", response.split(":")[-1]).group(1).split()
        self.channel_users[channel] = set(names)
        print(f"Users in {channel}: {', '.join(names)}")

    def send_message(self, target, message):
        """
        Sends a PRIVMSG to a target user or channel.

        :param target: The nickname or channel to which the message should be sent.
        :param message: The message to send.
        """
        self.socket.sendall(f"PRIVMSG {target} :{message}\n".encode())

    def request_user_list(self, channel):
        """
        Requests a list of users present in a channel by sending the NAMES command.

        :param channel: The channel for which to request the user list.
        """
        self.socket.sendall(f"NAMES {channel}\n".encode())
