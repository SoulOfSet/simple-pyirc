import logging
import re
import socket
import threading
from time import sleep
from typing import Callable


logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback: Callable):
        self.subscribers.append(callback)

    def publish(self, *args, **kwargs):
        for subscriber in self.subscribers:
            subscriber(*args, **kwargs)


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
        self.message_event = EventPublisher()
        self.user_event = EventPublisher()
        self.names_event = EventPublisher()

    def connect(self) -> bool:
        """
        Attempts to connect to the IRC server.

        :return: True if the connection was successful, False otherwise.
        """
        try:
            self.socket.connect((self.host, self.port))
            logger.info("Connected to IRC server.")
            self.connected = True
            self.start_listening()
            return True
        except Exception as e:
            logger.info(f"Failed to connect to IRC server: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Closes the connection to the IRC server.

        :return: True if the disconnection was successful, False otherwise.
        """
        try:
            self.socket.close()
            self.connected = False
            logger.info("Disconnected from IRC server.")
            return True
        except Exception as e:
            logger.info(f"Failed to disconnect from IRC server: {e}")
            return False

    def send_ping(self) -> bool:
        """
        Sends a PING command to the IRC server to check if it's responsive.

        :return: True if the PING was successfully sent and a response received, False otherwise.
        """
        try:
            self.socket.sendall(b"PING :ping\n")
            response = self.socket.recv(4096)
            logger.info(f"Received: {response}")
            return True
        except Exception as e:
            logger.info(f"Failed to send PING: {e}")
            return False

    def register(self, nickname: str) -> bool:
        """
        Registers the user with the IRC server using a specified nickname and predefined user information.

        :param nickname: The nickname to register with the IRC server.
        :return: True if the registration was successful, False otherwise.
        """
        if not self.connected:
            logger.info("You must connect before registering.")
            return False
        self.nickname = nickname
        try:
            self.socket.sendall(f"NICK {self.nickname}\n".encode())
            sleep(1)
            self.socket.sendall(f"USER {self.nickname} 0 * :{self.userinfo}\n".encode())
            # Wait for a response from the server
            response = self.socket.recv(4096).decode()
            logger.info(f"Registration response: {response}")
            return True
        except Exception as e:
            logger.info(f"Failed to register with IRC server: {e}")
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
                logger.info("Nickname collision, please choose another.")
                return False
            else:
                self.nickname = new_nickname
                logger.info(f"Nickname updated to {new_nickname}")
                return True
        except Exception as e:
            logger.info(f"Failed to update nickname: {e}")
            return False

    def join_channel(self, channel: str) -> bool:
        """
        Joins a specific channel.

        :param channel: The channel name to join.
        :return: True if the channel join attempt was made, False otherwise.
        """
        if not self.connected:
            logger.info("You must be connected to join a channel.")
            return False
        try:
            self.socket.sendall(f"JOIN {channel}\n".encode())
            self.channels.add(channel)  # Add to the internal set of channels
            logger.info(f"Attempted to join channel: {channel}")
            sleep(1)  # Allow some time for the server to respond
            self.request_user_list(channel)  # Request user list right after joining
            return True
        except Exception as e:
            logger.info(f"Failed to join channel {channel}: {e}")
            return False

    def leave_channel(self, channel: str) -> bool:
        """
        Leaves a specific channel.

        :param channel: The channel name to leave.
        :return: True if the channel leave attempt was made, False otherwise.
        """
        if not self.connected:
            logger.info("You must be connected to leave a channel.")
            return False
        try:
            self.socket.sendall(f"PART {channel}\n".encode())
            self.channels.discard(channel)  # Remove from the internal set of channels
            logger.info(f"Attempted to leave channel: {channel}")
            return True
        except Exception as e:
            logger.info(f"Failed to leave channel {channel}: {e}")
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
                    logger.info(f"Server says: {response}")
                    self.handle_server_response(response)
            except Exception as e:
                logger.info(f"Error listening to server: {e}")
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
        It differentiates between messages sent to a channel and private messages to the user.

        :param response: The raw response string from the server containing the PRIVMSG command.
        """
        sender = re.search(r":(\S+)!", response).group(1)
        channel_or_user = re.search(r"PRIVMSG (\S+)", response).group(1)
        message = re.search(r"PRIVMSG \S+ :(.+)", response).group(1)
        if channel_or_user.startswith('#'):
            logger.info(f"Message from {sender} in {channel_or_user}: {message}")
            self.message_event.publish(sender, channel_or_user, message)
        else:
            logger.info(f"Private message from {sender}: {message}")
            self.message_event.publish(sender, 'private', message)

    def handle_join(self, response):
        """
        Handles a JOIN message from the server. This method extracts the user who joined and the channel
        they joined, updates the internal mapping of channel users, and publishes the join event.

        :param response: The raw response string from the server containing the JOIN command.
        """
        user = re.search(r":(\S+)!", response).group(1)
        channel = re.search(r"JOIN (\S+)", response).group(1).replace(":", "")
        if channel not in self.channel_users:
            self.channel_users[channel] = set()
        self.channel_users[channel].add(user)
        logger.info(f"{user} has joined {channel}")
        self.user_event.publish(user, channel, "joined")

    def handle_part(self, response):
        """
        Handles a PART message from the server. This method extracts the user who left and the channel
        they left, updates the internal mapping of channel users, and publishes the part event.

        :param response: The raw response string from the server containing the PART command.
        """
        user = re.search(r":(\S+)!", response).group(1)
        channel = re.search(r"PART (\S+)", response).group(1)
        if channel in self.channel_users and user in self.channel_users[channel]:
            self.channel_users[channel].remove(user)
        logger.info(f"{user} has left {channel}")
        self.user_event.publish(user, channel, "left")

    def handle_names(self, response):
        """
        Handles the NAMES response from the server. This method extracts the channel name and the list of
        nicknames in that channel, then updates the internal mapping of channels to users.

        :param response: The raw response string from the server containing the NAMES list.
        """
        if '353' in response and '366' in response:
            # Find the start and end of the relevant part of the response
            start_index = response.find('353')
            end_index = response.find('366', start_index)

            # Extract the part of the response that contains the names list
            names_part = response[start_index:end_index]

            # Extract the channel name and names list
            parts = names_part.split()
            channel_index = parts.index('353') + 3  # The channel name follows the '353' marker by 4 positions
            channel = parts[channel_index]

            # Extract names; they are after the channel name, delimited by ':'
            names_start_index = names_part.find(':', names_part.find(channel)) + 1
            names_end_index = names_part.find(':', names_start_index)
            names = names_part[names_start_index:names_end_index].split()

            if channel not in self.channel_users:
                self.channel_users[channel] = set()

            # Update the entire set to match the NAMES response
            self.channel_users[channel] = set(names)

            logger.info(f"Updated user list for {channel}: {', '.join(names)}")
            # Publish names event to update UI components
            self.names_event.publish(channel, names)

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
